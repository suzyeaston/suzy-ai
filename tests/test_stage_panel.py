"""Hardware-free regression tests for the browser-controlled, non-exporting AI panel."""
from array import array
import http.client
import json
import threading
import time
import unittest
from unittest.mock import patch

from suzy_ai.music.stage_panel import StageEngine, PanelHandler, _validate_controls, _mic_mono, RATE


class FakeStream:
    def __init__(self, callback, channels):
        self.callback = callback
        self.channels = channels
        self.running = False
    def start(self): self.running=True
    def stop(self): self.running=False
    def close(self): self.running=False
    def tick(self, mic_pcm):
        frames=len(mic_pcm)//(self.channels[0]*2)
        output=bytearray(frames*4)
        self.callback(mic_pcm,output,frames,None,None)
        return bytes(output)


class FakeSoundDevice:
    def __init__(self): self.stream=None
    def query_devices(self):
        return [
            {"name":"Scarlett Solo USB","max_input_channels":2,"max_output_channels":2},
            {"name":"MacBook Pro Speakers","max_input_channels":0,"max_output_channels":2},
        ]
    def RawStream(self,**kwargs):
        self.stream=FakeStream(kwargs["callback"],kwargs["channels"])
        return self.stream


class Composer:
    def __init__(self): self.calls=[]
    def __call__(self, phrase, *, instruction, use_deep_research, accompaniment):
        self.calls.append((phrase,instruction,use_deep_research,accompaniment))
        return {"model":"mock_local_test_only", "bpm_supplied":phrase["bpm_supplied"],
                "duration_seconds":phrase["duration_seconds"],
                "events":[{"start_beats":0.5,"duration_beats":0.4,
                           "midi_note":65,"velocity":60}],
                "reference_used":"baduizm-1997-call-space" if use_deep_research else None,
                "references_offered":["baduizm-1997-call-space"] if use_deep_research else []}


def settings():
    return {"bpm":120,"beats":8,"instruction":"Baduizm R&B answer",
            "chord":"Am9","research":True}


def phrase():
    return {"status":"monophonic_candidate",
            "duration_seconds":4.0,"bpm_supplied":120,
            "notes":[{"midi_note":60,"confidence":.97,"start_beats":0},
                     {"midi_note":63,"confidence":.97,"start_beats":1.5}]}


def capture(engine, stream):
    # The mock route receives a non-silent mono mic on Scarlett channel 1.
    chunk=(array("h",[2000,0])*512).tobytes()
    while engine.status()["state"]=="capturing":
        stream.tick(chunk)


class StagePanelTests(unittest.TestCase):
    def setUp(self):
        self.audio=FakeSoundDevice()
        self.fake_model=Composer()
        self.engine=StageEngine(self.audio,composer=self.fake_model)
    def tearDown(self):
        self.engine.close()

    def connect(self):
        return self.engine.connect({"input_id":0,"output_id":1,"mic_channel":1})

    def test_live_capture_to_local_model_and_audition_without_files(self):
        self.connect()
        self.engine.arm(settings())
        with patch("suzy_ai.music.stage_panel.extract_phrase",return_value=phrase()):
            capture(self.engine,self.audio.stream)
            deadline=time.monotonic()+3
            while self.engine.status()["state"] in ("captured","processing") and time.monotonic()<deadline:
                time.sleep(.015)
        status=self.engine.status()
        self.assertEqual(status["state"],"ready",status["error"])
        self.assertEqual(status["notes"][0]["midi_note"],65)
        self.assertTrue(status["peak"]>.05)
        self.assertEqual(self.fake_model.calls[0][2],True)
        self.assertEqual(self.fake_model.calls[0][3]["chord"],"Am9")
        self.assertEqual(self.fake_model.calls[0][3]["half_beat_energy"],[])
        self.engine.audition(1)
        result=self.audio.stream.tick(bytes(512*4))
        self.assertEqual(len(result),512*4)
        self.assertTrue(any(result))
        self.engine.stop()
        self.assertEqual(self.engine.status()["state"],"idle")
        self.assertEqual(self.audio.stream.tick(bytes(512*4)),bytes(512*4))

    def test_stop_during_inference_prevents_late_response(self):
        self.connect()
        self.engine.arm(settings())
        class LateComposer:
            def __call__(self,*a,**kw):
                time.sleep(.12)
                return Composer()(*a,**kw)
        self.engine.composer=LateComposer()
        with patch("suzy_ai.music.stage_panel.extract_phrase",return_value=phrase()):
            capture(self.engine,self.audio.stream)
            deadline=time.monotonic()+2
            while self.engine.status()["state"]!="processing" and time.monotonic()<deadline:
                time.sleep(.01)
            self.engine.stop()
            time.sleep(.25)
        self.assertEqual(self.engine.status()["state"],"idle")
        self.assertEqual(self.engine.status()["notes"],[])

    def test_invalid_controls_never_arm_audio(self):
        self.connect()
        for value in (0,1,240.1,float("nan"),True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                _validate_controls({**settings(),"bpm":value})
        with self.assertRaises(ValueError):
            self.engine.arm({**settings(),"beats":16,"bpm":60})  # > 8s
        with self.assertRaises(ValueError):
            self.engine.connect({"input_id":0,"output_id":1,"mic_channel":3})
        self.assertEqual(self.engine.status()["state"],"idle")

    def test_selected_mic_channel_is_not_mixed_with_silence(self):
        pcm=(array("h",[1000,0,2000,0])).tobytes()
        mono=_mic_mono(pcm,2,0)
        decoded = array("h")
        decoded.frombytes(mono)
        self.assertEqual(decoded.tolist(),[1000,2000])
        silent = array("h")
        silent.frombytes(_mic_mono(pcm,2,1))
        self.assertEqual(silent.tolist(),[0,0])

    def test_browser_post_requires_origin_and_random_token(self):
        class Handler(PanelHandler):
            pass
        Handler.engine=self.engine
        Handler.token="fixed_unit_test_secret_token"
        from http.server import ThreadingHTTPServer
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        server.daemon_threads=True
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        try:
            c=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=2)
            c.request("POST","/api/stop",body="{}",headers={"Content-Type":"application/json"})
            self.assertEqual(c.getresponse().status,403)
            c.close()
            c=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=2)
            c.request("POST","/api/stop",body="{}",headers={"Content-Type":"application/json",
                "X-Suzy-Panel-Token":Handler.token,
                "Origin":"https://attacker.example"})
            self.assertEqual(c.getresponse().status,403)
            c.close()
            c=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=2)
            c.request("POST","/api/stop",body="{}",headers={"Content-Type":"application/json",
                "X-Suzy-Panel-Token":Handler.token,
                "Origin":f"http://127.0.0.1:{server.server_port}"})
            self.assertEqual(c.getresponse().status,200)
            c.close()
        finally:
            server.shutdown();server.server_close();worker.join()


if __name__=="__main__":
    unittest.main()
