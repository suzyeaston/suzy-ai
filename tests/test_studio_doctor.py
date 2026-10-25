"""No-hardware QA for conservative studio preflight."""
import unittest
from suzy_ai.music.studio_doctor import inspect


class StudioDoctorTests(unittest.TestCase):
    def test_positive_hardware_observations_never_claim_ready(self):
        calls = []
        def fake(argv):
            calls.append(argv)
            if argv[0] == "pluginkit":
                return "MRT2_AU.appex (Google Magenta)"
            return None
        result = inspect(system="Darwin", machine="arm64", run=fake,
                         audio_names=["Scarlett Solo USB"],
                         midi_names=["Keystation Mini 32 MK3"])
        by_name = {x["name"]: x for x in result["checks"]}
        self.assertEqual(by_name["Apple Silicon macOS"]["status"], "PASS")
        self.assertEqual(by_name["MRT2 Audio Unit"]["status"], "PASS")
        self.assertEqual(by_name["AI audio bounced, saved, reopened"]["status"], "CHECK")
        self.assertFalse(result["ready"])
        self.assertTrue(any(cmd[0] == "pluginkit" for cmd in calls))

    def test_non_mac_skips_mac_processes(self):
        def forbidden(_):
            raise AssertionError("macOS command invoked on Linux")
        result = inspect(system="Linux", machine="x86_64", run=forbidden,
                         audio_names=[], midi_names=[])
        self.assertEqual(result["checks"][0]["status"], "FAIL")
        self.assertFalse(result["ready"])

    def test_missing_registry_and_devices_are_not_false_positive(self):
        result = inspect(system="Darwin", machine="arm64", run=lambda _:None,
                         audio_names=[], midi_names=[])
        statuses = {x["name"]:x["status"] for x in result["checks"]}
        self.assertEqual(statuses["Scarlett audio interface"], "WARN")
        self.assertEqual(statuses["Keystation MIDI controller"], "WARN")
        self.assertEqual(statuses["MRT2 Audio Unit"], "CHECK")
        self.assertFalse(result["ready"])

    def test_case_insensitive_device_matches(self):
        result = inspect(system="Darwin", machine="arm64", run=lambda _:"",
                         audio_names=["FOCUSRITE SCARLETT"], midi_names=["MAudio KEYSTATION"])
        statuses = {x["name"]:x["status"] for x in result["checks"]}
        self.assertEqual(statuses["Scarlett audio interface"], "PASS")
        self.assertEqual(statuses["Keystation MIDI controller"], "PASS")


if __name__ == "__main__":
    unittest.main()
