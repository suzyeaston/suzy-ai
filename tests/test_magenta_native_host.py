"""Native MRT2 bridge guards: no model starts without explicit performer action."""
from pathlib import Path
import unittest
from unittest.mock import patch
from suzy_ai.music.magenta_native_host import NativeMagentaHost, PROMPTS, ACTIONS


class NativeMRT2Tests(unittest.TestCase):
    def setUp(self):
        self.host = NativeMagentaHost(binary=Path("/nonexistent/MRT2"))

    def tearDown(self):
        self.host.close()

    def test_native_does_not_start_while_browser_is_open(self):
        self.assertEqual(self.host.status()["phase"], "not-running")
        self.assertFalse(self.host.status()["model_audio_confirmed"])
        self.assertFalse(self.host.status()["build_available"])
        self.assertIsNone(self.host.process)
        self.assertIn("pyramid", PROMPTS)
        self.assertIn("fishes", PROMPTS)
        self.assertNotEqual(PROMPTS["pyramid"], PROMPTS["fishes"])

    def test_reject_invalid_controls_without_forking_model(self):
        invalid = [
            ("chord", {"index": True}), ("chord", {"index": 4}),
            ("scene", {"scene":"bad"}), ("mix", {"value":2}),
            ("mix", {"value":"0.3"}), ("volume", {"value":-1}),
            ("mute", {"value":1}), ("start", {"model":"remote"}),
            ("release", {"index":1}), ("other",{}),
            ("tempo", {"bpm": 240}), ("tempo", {"bpm": True}),
            ("note", {"note": -1}), ("note", {"note": 128}),
            ("note-off", {"note": "60"}),
        ]
        for cmd,data in invalid:
            with self.subTest(action=cmd, data=data), self.assertRaises(ValueError):
                self.host.command(cmd, data)
        self.assertIsNone(self.host.process)

    def test_start_is_only_user_initiated_and_requires_binary(self):
        with patch("suzy_ai.music.magenta_native_host.platform.system", return_value="Darwin"):
            with self.assertRaisesRegex(RuntimeError, "not built"):
                self.host.command("start", {})
        self.assertIsNone(self.host.process)

    def test_distinct_real_native_actions_have_explicit_schemas(self):
        for op in ("start", "stop", "status", "scene", "mix", "volume", "mute", "chord", "release", "tempo", "note", "note-off"):
            self.assertIn(op, ACTIONS)
        self.assertEqual(ACTIONS["chord"], {"index"})
        self.assertEqual(ACTIONS["scene"], {"scene"})
        self.assertEqual(ACTIONS["mute"], {"value"})
        self.assertEqual(ACTIONS["tempo"], {"bpm"})
        self.assertEqual(ACTIONS["note"], {"note"})


if __name__ == "__main__":
    unittest.main()
