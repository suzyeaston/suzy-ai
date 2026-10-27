"""HTTP tests: guarded TOASTER computer-keyboard endpoints and honest state."""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from suzy_ai.music.magenta_stage import MagentaStageHandler
from suzy_ai.music.magenta_midi import MagentaMidiBridge
from suzy_ai.music.toaster_performance import ToasterPerformance
from tests.test_magenta_midi import FakeRtMidi


class LiveToasterHttpTests(unittest.TestCase):
    def setUp(self):
        class Handler(MagentaStageHandler):
            pass
        self.bridge = MagentaMidiBridge(FakeRtMidi())
        self.perf = ToasterPerformance(self.bridge)
        Handler.bridge = self.bridge
        Handler.performance = self.perf
        Handler.token = "test-live-token"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.perf.close()
        self.bridge.close()

    def call(self, method, route, body=None, token=True, origin=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {}
        if method == "POST":
            headers["Content-Type"] = "application/json"
            if token:
                headers["X-Suzy-Token"] = "test-live-token"
            if origin:
                headers["Origin"] = origin
        conn.request(method, route, json.dumps(body if body is not None else {}) if method == "POST" else None, headers)
        r = conn.getresponse()
        raw = r.read()
        status = r.status
        conn.close()
        if raw.startswith(b"{"):
            return status, json.loads(raw)
        return status, raw.decode("utf-8")

    def test_live_page_is_local_and_keyboard_playable(self):
        status, html = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//TOAST", html)
        self.assertIn("test-live-token", html)
        self.assertIn("data-pad=", html)
        self.assertIn("navigator.mediaDevices.getUserMedia", html)
        self.assertIn("MediaRecorder", html)
        self.assertIn("real rehearsal verification", html)
        self.assertNotIn("__MAGENTA_TOKEN__", html)

    def test_authorized_pads_work_without_physical_input(self):
        self.assertIsNone(self.bridge.source)
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0}, token=False)[0],403)
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0},origin="https://attacker.example")[0],403)
        code, data = self.call("POST", "/api/perform/chord", {"index":0})
        self.assertEqual(code, 200)
        self.assertEqual(data["chord_index"], 0)
        self.assertFalse(data["magenta_audio_confirmed"])
        self.assertIn([0x91, 54, 56], self.bridge.output.messages)
        self.assertEqual(self.call("POST", "/api/perform/scene", {"scene":"fishes"})[1]["scene"],"fishes")
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[1]["chords"][0],"Em7")

    def test_rhythm_and_release_do_not_claim_audio_mute(self):
        self.call("POST", "/api/perform/chord", {"index":0})
        self.assertEqual(self.call("POST", "/api/perform/settings", {"bpm":132,"rhythm":"pulse","intensity":75})[0],200)
        self.assertEqual(self.call("POST", "/api/perform/start")[1]["running"],True)
        code, status = self.call("POST", "/api/release")
        self.assertEqual(code, 200)
        self.assertEqual(self.perf.status()["running"],False)
        self.assertEqual(status["ai_audio_muted"],"not_observed")
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":True})[0],400)
        self.assertEqual(self.call("POST", "/api/perform/settings", {"bpm":0,"rhythm":"pulse","intensity":50})[0],400)


if __name__=="__main__":
    unittest.main()
