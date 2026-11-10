"""HTTP safety contract for separate Magenta MIDI-only stage surface."""
import http.client
import threading
import unittest
from unittest.mock import patch, Mock
from http.server import ThreadingHTTPServer

from suzy_ai.music.magenta_stage import MagentaStageHandler, PAGE
from tests.test_magenta_midi import FakeRtMidi
from suzy_ai.music.magenta_midi import MagentaMidiBridge


class StageHttpTests(unittest.TestCase):
    def setUp(self):
        class Handler(MagentaStageHandler):
            pass
        self.bridge = MagentaMidiBridge(FakeRtMidi())
        Handler.bridge = self.bridge
        Handler.token = "unit-test-local-token"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.bridge.close()

    def request(self, method, route, data=None, token=True, origin=None):
        import json
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        headers = {}
        if method == "POST":
            headers["Content-Type"] = "application/json"
            if token:
                headers["X-Suzy-Token"] = "unit-test-local-token"
            if origin is not None:
                headers["Origin"] = origin
        conn.request(method, route, body=json.dumps(data or {}) if method == "POST" else None,
                     headers=headers)
        response = conn.getresponse()
        raw = response.read()
        status = response.status
        conn.close()
        return status, json.loads(raw) if raw.startswith(b"{") else raw.decode("utf8")

    def test_route_and_content_security(self):
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//AI", html)
        self.assertIn("unit-test-local-token", html)
        self.assertIn("RELEASE MIDI", html)
        self.assertNotIn("MRT2 AUDIO CONNECTED", html)
        status, data = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(data["magenta_connection"], "not_observed")
        self.assertEqual(self.request("GET", "/other")[0], 404)

    def test_toaster_preview_is_served_without_fake_logic_controls(self):
        status, html = self.request("GET", "/toaster")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//TOAST", html)
        self.assertIn("unit-test-local-token", html)
        self.assertNotIn("__MAGENTA_TOKEN__", html)
        self.assertIn('id="lever"', html)
        self.assertIn('id="heat"', html)
        self.assertIn('data-mode="direct"', html)
        self.assertIn('"/api/test"', html)
        self.assertIn('"/api/gate"', html)
        self.assertIn('"/api/release"', html)
        self.assertIn("CC 21", html)
        self.assertIn("CC 26", html)
        self.assertIn("not yet a loadable Logic AUv3", html)
        self.assertIn("mute the", html.lower())
        self.assertNotIn("MRT2 AUDIO CONNECTED", html)
        self.assertNotIn('e.code==="Space"', html)

    def test_toaster_uses_existing_protected_midi_commands(self):
        status, _ = self.request("GET", "/toaster")
        self.assertEqual(status, 200)
        self.assertEqual(self.request("POST", "/api/test", token=False)[0], 403)
        self.assertEqual(self.request("POST", "/api/test", origin="https://evil.example")[0], 403)
        self.assertEqual(self.request("POST", "/api/test")[0], 200)
        self.assertGreater(self.bridge.status()["midi_messages_sent"], 0)
        self.assertEqual(self.request("POST", "/api/gate", {"open": False})[0], 200)
        self.assertEqual(self.request("POST", "/api/test")[0], 400)
        self.assertEqual(self.request("POST", "/api/release")[0], 200)

    def test_token_and_origin_required_for_commands(self):
        self.assertEqual(self.request("POST", "/api/test", token=False)[0], 403)
        self.assertEqual(self.request("POST", "/api/test", origin="https://evil.example")[0], 403)
        self.assertEqual(self.bridge.status()["midi_messages_sent"], 0)
        allowed = f"http://127.0.0.1:{self.server.server_port}"
        self.assertEqual(self.request("POST", "/api/mode",
                                      {"mode": "high"}, origin=allowed)[0], 200)
        self.assertEqual(self.bridge.status()["mode"], "high")

    def test_connect_gate_release_and_validation(self):
        status, inputs = self.request("GET", "/api/inputs")
        self.assertEqual(status, 200)
        self.assertEqual(inputs["inputs"], ["Keystation Mini 32 MK3"])
        self.assertEqual(self.request("POST", "/api/select",
                                      {"input": "Keystation Mini 32 MK3"})[0], 200)
        status, gate = self.request("POST", "/api/gate", {"open": False})
        self.assertEqual(status, 200)
        self.assertFalse(gate["gate_open"])
        self.assertEqual(self.request("POST", "/api/test")[0], 400)
        self.assertEqual(self.request("POST", "/api/gate", {"open": True})[0], 200)
        self.assertEqual(self.request("POST", "/api/release")[0], 200)
        self.assertEqual(self.request("POST", "/api/disconnect")[0], 200)
        self.assertEqual(self.request("POST", "/api/mode", {"mode": "fake"})[0], 400)
        self.assertEqual(self.request("POST", "/api/mode", {"mode": "low", "unused": True})[0], 400)

    def test_audio_routing_api_is_read_only_and_cannot_claim_logic_selection(self):
        with patch("suzy_ai.music.magenta_stage.inspect_audio_routing", return_value={
            "available": True,
            "devices": [{"id": 0, "name": "Scarlett Solo USB",
                         "input_channels": 2, "output_channels": 2,
                         "system_default_input": True, "system_default_output": True,
                         "scarlett_candidate": True}],
            "logic_audio_device_observed": False,
            "magenta_audio_observed": False,
            "can_change_host_audio_output": False,
        }):
            status, data = self.request("GET", "/api/audio-routing")
        self.assertEqual(status, 200)
        self.assertEqual(data["devices"][0]["name"], "Scarlett Solo USB")
        self.assertFalse(data["logic_audio_device_observed"])
        self.assertFalse(data["can_change_host_audio_output"])
        self.assertEqual(self.request("POST", "/api/audio-routing", {"device": 0})[0], 404)

    def test_full_five_prompt_bank_reaches_native_host_instead_of_http_413(self):
        # Regression: the Film Club five-string request is > 2 KiB,
        # previously blocked by the stage before native AI code ran.
        import json
        from suzy_ai.music.film_club_pyramid import FILM_PROMPTS
        from suzy_ai.music.magenta_stage import (
            CONTROL_JSON_MAX_BYTES, PROMPT_JSON_MAX_BYTES
        )
        payload = {"prompts": list(FILM_PROMPTS)}
        byte_length = len(json.dumps(payload).encode("utf8"))
        self.assertGreater(byte_length, CONTROL_JSON_MAX_BYTES)
        self.assertLess(byte_length, PROMPT_JSON_MAX_BYTES)
        fake = Mock()
        fake.command.return_value = {"phase": "initializing"}
        self.server.RequestHandlerClass.native_host = fake
        status, result = self.request("POST", "/api/ai/reload-prompts", payload)
        self.assertEqual(status, 200, result)
        self.assertEqual(result["phase"], "initializing")
        fake.command.assert_called_once_with("reload-prompts", payload)

    def test_large_prompt_json_is_allowed_only_for_prompt_endpoints(self):
        from suzy_ai.music.magenta_stage import PROMPT_JSON_MAX_BYTES
        fake = Mock()
        fake.command.return_value = {"phase": "initializing"}
        self.server.RequestHandlerClass.native_host = fake
        bank = {"prompts": ["synth " + "a" * 475 for _ in range(5)]}
        for route, action in (
            ("/api/ai/reload-prompts", "reload-prompts"),
            ("/api/ai/configure-prompts", "configure-prompts"),
            ("/api/ai/start", "start"),
        ):
            with self.subTest(route=route):
                status, result = self.request("POST", route, bank)
                self.assertEqual(status, 200, result)
                fake.command.assert_called_with(action, bank)
        # Non-prompt actions retain their original 2048 byte cap.
        fake.reset_mock()
        status, result = self.request("POST", "/api/test",
                                      {"padding": "a" * 2500})
        self.assertEqual(status, 413)
        self.assertIn("2048 bytes", result["error"])
        fake.command.assert_not_called()
        # A huge prompt request is still refused before touching AI.
        status, result = self.request(
            "POST", "/api/ai/reload-prompts",
            {"prompts": ["x" * PROMPT_JSON_MAX_BYTES] * 5}
        )
        self.assertEqual(status, 413)
        self.assertIn(str(PROMPT_JSON_MAX_BYTES), result["error"])
        fake.command.assert_not_called()

    def test_large_prompt_endpoint_keeps_authentication_and_origin_checks(self):
        from suzy_ai.music.film_club_pyramid import FILM_PROMPTS
        fake = Mock()
        self.server.RequestHandlerClass.native_host = fake
        payload = {"prompts": list(FILM_PROMPTS)}
        self.assertEqual(self.request("POST", "/api/ai/reload-prompts",
                                      payload, token=False)[0], 403)
        self.assertEqual(self.request("POST", "/api/ai/reload-prompts",
                                      payload, origin="https://wrong.example")[0], 403)
        fake.command.assert_not_called()

    def test_static_ui_refuses_fictional_audio_controls(self):
        html = PAGE.read_text(encoding="utf8")
        self.assertIn('id="gate"', html)
        self.assertIn('id="release"', html)
        self.assertIn('data-mode="direct"', html)
        self.assertIn("does not", html.lower())
        self.assertIn('id="audioSetup"', html)
        self.assertIn('id="refreshAudio"', html)
        self.assertIn('"/api/audio-routing"', html)
        self.assertIn("Logic Pro", html)
        self.assertIn("Scarlett", html)
        self.assertNotIn('e.code==="Space"', html)
        self.assertNotIn('e.key==="Enter"', html)


if __name__ == "__main__":
    unittest.main()
