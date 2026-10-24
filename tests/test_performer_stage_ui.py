"""Contract for performer-first stage layout without changing audio backend."""
from pathlib import Path
import unittest

from suzy_ai.music import stage_panel


class PerformerPanelTests(unittest.TestCase):
    def test_main_controls_have_same_ids_expected_by_backend_and_previous_panel(self):
        html=stage_panel.PAGE.read_text(encoding="utf8")
        for control in ("capture", "play", "stop", "connect", "test",
                        "inputDevice", "outputDevice", "channel", "research",
                        "bpm", "beats", "chord", "countdown", "feedback", "error"):
            with self.subTest(control=control):
                self.assertIn('id="'+control+'"',html)
        self.assertIn('__SUZY_PANEL_TOKEN__',html)
        for route in ("/api/connect","/api/arm","/api/audition",
                      "/api/stop","/api/test","/api/status","/api/devices"):
            self.assertIn(route,html)

    def test_easy_performance_roles_not_fake_backends(self):
        html=stage_panel.PAGE.read_text(encoding="utf8")
        for role in ('data-role="space"','data-role="answer"',
                     'data-role="counter"'):
            self.assertIn(role,html)
        for phrase in ("SPACE", "ANSWER", "COUNTERLINE",
                       "STOP AI", "Audio setup", "Diagnostics"):
            self.assertIn(phrase,html)
        # No unsupported 'magenta is working right now' indicator.
        self.assertIn("not connected to this panel",html)
        self.assertIn("Logic",html)
        # Existing Qwen API takes an instruction string; ensure roles map to text.
        self.assertIn("instruction:roles[role]",html)
        self.assertIn('research:el("research").checked',html)

    def test_musician_shortcuts_and_safe_cancel(self):
        html=stage_panel.PAGE.read_text(encoding="utf8")
        for shortcut in ('e.key==="1"','e.key==="2"','e.key==="3"',
                         'e.code==="Space"','e.key==="Enter"',
                         'e.key==="Escape"'):
            self.assertIn(shortcut,html)
        self.assertIn('clearTimeout(countdown)',html)
        self.assertIn('if(countdown===null)draw(x)',html)
        self.assertIn('s.state==="ready"',html)
        self.assertIn('s.state==="capturing"',html)
        self.assertIn('el("play").disabled=s.state!=="ready"',html)

    def test_backend_controls_and_hardware_untouched(self):
        result=stage_panel._validate_controls({
            "bpm":92,"beats":8,"chord":"Am9","research":True,
            "instruction":"Compose a fresh vocal answer."
        })
        self.assertEqual(result["seconds"],8*60/92)
        self.assertEqual(result["chord"],"Am9")


if __name__=="__main__":
    unittest.main()
