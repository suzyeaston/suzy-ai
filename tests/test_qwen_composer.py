"""Offline HTTP contract and note-safety tests for the Qwen composer."""
import http.client
import io
import json
import threading
import time
import unittest
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from suzy_ai.music.counterline import audition_wav
from suzy_ai.music.qwen_composer import (
    CompositionError, LocalQwenComposer, _phrase_context, validate_generated_notes,
)


def phrase():
    return {"status":"monophonic_candidate","bpm_supplied":100,
            "duration_seconds":4,
            "notes":[{"midi_note":60,"confidence":.96,"start_beats":0},
                     {"midi_note":64,"confidence":.96,"start_beats":1.5},
                     {"midi_note":67,"confidence":.96,"start_beats":3}]}


def start_fake():
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            incoming=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(incoming)
            if self.server.stall:
                time.sleep(.4)
            if self.server.code != 200:
                self.send_response(self.server.code)
                self.end_headers()
                return
            payload={"model":"fake-local-model","message":{"role":"assistant",
                "content":json.dumps(self.server.answer)}}
            data=json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            try: self.wfile.write(data)
            except BrokenPipeError: pass
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    server.stall=False
    server.code=200
    server.answer={"notes":[[0.5,67,0.5,70],[1.5,62,0.5,65]],"used_reference":None}
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    return server,thread,requests


class QwenComposerTests(unittest.TestCase):
    def test_local_model_changes_actual_synthesized_notes(self):
        server,thread,requests=start_fake()
        try:
            composer=LocalQwenComposer(f"http://127.0.0.1:{server.server_address[1]}/v1")
            first=composer(phrase(),instruction="Original R&B answer")
            self.assertEqual(first["model"],"fake-local-model")
            self.assertEqual([n["midi_note"] for n in first["events"]],[67,62])
            self.assertEqual(first["references_offered"],[])
            self.assertEqual(requests[0]["use_memory"],False)
            self.assertEqual(requests[0]["history"],[])
            self.assertNotIn("historical_context",requests[0]["message"])
            a=audition_wav(first)
            server.answer={"notes":[[0.75,72,0.6,70],[2.25,65,0.35,55]],"used_reference":None}
            second=composer(phrase(),instruction="Original R&B answer")
            b=audition_wav(second)
            self.assertNotEqual(a,b)
            with wave.open(io.BytesIO(a)) as wav:
                self.assertEqual((wav.getframerate(),wav.getnchannels()),(48000,2))
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_source_provenance_can_be_offered_and_cited_but_not_invented(self):
        server,thread,requests=start_fake()
        try:
            server.answer={"notes":[[0.5,67,0.5,70]],"used_reference":"illmatic-1994"}
            composer=LocalQwenComposer(f"http://127.0.0.1:{server.server_address[1]}/v1")
            grounded=composer(phrase(),instruction="Illmatic boom bap piano",use_era_knowledge=True)
            self.assertEqual(grounded["reference_used"],"illmatic-1994")
            self.assertIn("illmatic-1994",grounded["references_offered"])
            self.assertIn("historical_reference_cards",requests[-1]["message"])
            self.assertIn("illmatic-1994",requests[-1]["message"])
            with self.assertRaisesRegex(CompositionError,"unprovided"):
                composer(phrase(),instruction="Illmatic",use_era_knowledge=False)
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_bad_or_copied_melody_is_never_played(self):
        context=_phrase_context(phrase())
        cases=[
            {"notes":[[.5,60,.5,80],[1.5,64,.5,80],[2.5,67,.5,80]],"used_reference":None},
            {"notes":[[0,60,1,80]],"used_reference":None},
            {"notes":[[.5,60,1,80],[1,64,1,80]],"used_reference":None},
            {"notes":[[.5,True,.5,80]],"used_reference":None},
            {"notes":[[.5,60,float("nan"),80]],"used_reference":None},
            {"notes":[[.5,60,20,80]],"used_reference":None},
            {"notes":[[.5,60,.5,101]],"used_reference":None},
            {"notes":[],"used_reference":None},
            {"notes":[[.5,65,.5,70]],"used_reference":"fake-album"},
            {"pattern":"stutter"},
        ]
        for case in cases:
            with self.subTest(case=case),self.assertRaises(CompositionError):
                validate_generated_notes(case,context)
        server,thread,_=start_fake()
        try:
            server.answer={"pattern":"vocal-echo"}
            composer=LocalQwenComposer(f"http://127.0.0.1:{server.server_address[1]}/v1")
            with self.assertRaises(CompositionError):
                composer(phrase())
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_confident_vocal_required_before_inference(self):
        server,thread,requests=start_fake()
        try:
            composer=LocalQwenComposer(f"http://127.0.0.1:{server.server_address[1]}/v1")
            p=phrase()
            p["notes"][0]["confidence"]=0.1
            p["notes"][1]["confidence"]=0.1
            with self.assertRaisesRegex(CompositionError,"too few"):
                composer(p)
            self.assertEqual(requests,[])
            with self.assertRaises(ValueError):
                LocalQwenComposer("https://remote.example/v1")
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_model_failure_has_no_presets_as_fallback(self):
        server,thread,_=start_fake()
        try:
            composer=LocalQwenComposer(f"http://127.0.0.1:{server.server_address[1]}/v1",timeout=.1)
            server.code=503
            with self.assertRaisesRegex(CompositionError,"503"):
                composer(phrase())
            server.code=200
            server.stall=True
            with self.assertRaises(CompositionError):
                composer(phrase())
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=="__main__":
    unittest.main()
