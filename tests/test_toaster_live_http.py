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
        status, html = self.call("GET", "/toaster/studio")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//TOAST", html)
        self.assertIn("test-live-token", html)
        self.assertIn("data-pad=", html)
        self.assertIn("navigator.mediaDevices.getUserMedia", html)
        self.assertIn("MediaRecorder", html)
        self.assertIn("CONNECT COLLIDER DIRECT",html)
        self.assertIn("real rehearsal verification", html)
        self.assertNotIn("__MAGENTA_TOKEN__", html)

    def test_owned_loop_rack_js_and_visible_three_lane_controls(self):
        status, html = self.call("GET", "/toaster/studio")
        self.assertEqual(status, 200)
        self.assertIn('<script src="/toaster/loop-rack.js"></script>', html)
        for name in ("rackChord", "rackVocal", "rackAI", "rackImport",
                     "rackLayers", "rackExport", "rackProgress"):
            self.assertIn(f'id="{name}"', html)
        self.assertIn("VE-22", html)
        self.assertIn("Actual AI only:", html)
        status, js = self.call("GET", "/toaster/loop-rack.js")
        self.assertEqual(status, 200)
        self.assertIn("root.SuzyLoopRack=Rack", js)
        self.assertIn("MediaRecorder", js)
        self.assertIn("getDisplayMedia", js)
        self.assertIn("decodeAudioData", js)

    def test_new_simple_play_is_default_and_presets_are_honest(self):
        status, html = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//TOAST", html)
        self.assertIn("Smiling pink toaster", html)
        self.assertIn('id="rhythm"', html)
        self.assertIn('id="deck-pyramid"', html)
        self.assertIn('id="deck-fishes"', html)
        self.assertIn("LOOP MY CHORDS", html)
        self.assertIn("LOOP VOICE", html)
        self.assertIn("auto Scarlett", html)
        self.assertIn("MRT2 prompt:", html)
        self.assertIn("ENABLE MAGENTA", html)
        self.assertIn('id="aiGoogleModel"', html)
        self.assertIn('id="aiTransport"', html)
        self.assertIn('aiFetch(on?"transport-pause":"transport-play")', html)
        self.assertIn('s.transport_playing===true', html)
        self.assertIn('id="aiModelHelp"', html)
        self.assertIn('s.native_model_selection_required!==true', html)
        self.assertIn('state.native_au_ui_visible', html)
        self.assertIn('s.native_au_ui_error', html)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))', html)
        self.assertIn('aiFetch("show-au-ui")', html)
        self.assertIn('native_model_selection_required', html)
        self.assertIn("Model audio must be tested by ear", html)
        self.assertIn("OfflineAudioContext", html)
        self.assertIn("function midi(which,index)", html)
        self.assertIn("function midiRelease()", html)
        self.assertIn("SCENES=", html)
        self.assertIn("VE-22", html)
        self.assertIn("Native Google Magenta AU is optional", html)
        self.assertNotIn("__MAGENTA_TOKEN__", html)
        self.assertNotIn("CONNECT COLLIDER DIRECT", html)
        self.assertNotIn("AUDIO ROUTING + MIXER", html)

    def test_live_arranger_is_editable_and_served_locally(self):
        status, html = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for needle in ('id="arrCues"', 'id="arrArm"', 'id="arrNext"',
                       'id="arrProgress"', 'window.SuzyArrangement',
                       'arranger.onCycle(count/8)', 'onCue:c=>', 'onChord:c=>'):
            self.assertIn(needle, html)
        code, js = self.call("GET", "/toaster/arrangement.js")
        self.assertEqual(code, 200)
        self.assertIn("root.SuzyArrangement=Arrangement", js)
        self.assertIn('root.localStorage.setItem(KEY', js)
        self.assertIn("this.endBar=bar+this.cues[0].bars", js)
        self.assertIn("this.skip=true", js)
        self.assertNotIn("eval(", js)

    def test_authorized_pads_work_without_physical_input(self):
        self.assertIsNone(self.bridge.source)
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0}, token=False)[0],403)
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0},origin="https://attacker.example")[0],403)
        code, data = self.call("POST", "/api/perform/chord", {"index":0})
        self.assertEqual(code, 200)
        self.assertEqual(data["chord_index"], 0)
        self.assertFalse(data["magenta_audio_confirmed"])
        self.assertIn([0x90, 54, 56], self.bridge.output.messages)
        self.assertEqual(self.call("POST", "/api/perform/scene", {"scene":"fishes"})[1]["scene"],"fishes")
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[1]["chords"][0],"Em7")

    def test_direct_collider_route_is_explicit_token_guarded_and_audio_unverified(self):
        self.assertEqual(self.call("POST", "/api/collider/connect", token=False)[0], 403)
        self.assertEqual(self.call("POST", "/api/collider/connect",
                                   origin="https://other.example")[0], 403)
        self.assertEqual(self.call("POST", "/api/collider/connect", {"ignored": True})[0], 400)
        status, body = self.call("POST", "/api/collider/connect")
        self.assertEqual(status, 200)
        self.assertTrue(body["collider_direct_ready"])
        self.assertEqual(body["collider_direct_output"], "MRT2 - Collider Input")
        self.assertFalse(body["magenta_audio_confirmed"])
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[0],200)
        self.assertIn([0x90, 54, 56],self.bridge.collider_out.messages)
        self.assertEqual(self.call("POST", "/api/collider/disconnect")[1]["collider_direct_ready"],False)
        self.assertFalse(self.perf.status()["collider_direct_ready"])

    def test_releasing_computer_key_sends_midi_note_off(self):
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[0], 200)
        self.assertEqual(self.call("POST", "/api/perform/release-chord", token=False)[0], 403)
        self.assertEqual(self.call("POST", "/api/perform/release-chord", {"index":0})[0], 400)
        code, data = self.call("POST", "/api/perform/release-chord", {})
        self.assertEqual(code, 200)
        self.assertIsNone(data["chord_index"])
        self.assertIn([0x80, 54, 0], self.bridge.output.messages)

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
