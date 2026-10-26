"""Read-only device discovery contract for music host setup."""
import unittest
from suzy_ai.music.audio_routing import inspect_audio_routing


class FakeSD:
    class Defaults:
        device = [0, 1]
    default = Defaults()

    def query_devices(self):
        return [
            {"name": "Scarlett Solo USB", "max_input_channels": 2,
             "max_output_channels": 2},
            {"name": "Built-in Output", "max_input_channels": 0,
             "max_output_channels": 2},
            {"name": "Input Only", "max_input_channels": 1,
             "max_output_channels": 0},
        ]


class FailedSD:
    class Defaults:
        device = (-1, -1)
    default = Defaults()

    def query_devices(self):
        raise OSError("Audio backend absent")


class AudioRoutingTests(unittest.TestCase):
    def test_separate_input_output_capabilities_and_default_markers(self):
        result = inspect_audio_routing(FakeSD())
        self.assertTrue(result["available"])
        self.assertEqual(len(result["devices"]), 3)
        scarlett = result["devices"][0]
        self.assertTrue(scarlett["scarlett_candidate"])
        self.assertTrue(scarlett["system_default_input"])
        self.assertFalse(scarlett["system_default_output"])
        self.assertTrue(result["devices"][1]["system_default_output"])
        self.assertEqual(result["devices"][2]["output_channels"], 0)
        self.assertFalse(result["logic_audio_device_observed"])
        self.assertFalse(result["magenta_audio_observed"])
        self.assertFalse(result["can_change_host_audio_output"])

    def test_query_failure_never_claims_routing(self):
        data = inspect_audio_routing(FailedSD())
        self.assertFalse(data["available"])
        self.assertEqual(data["devices"], [])
        self.assertFalse(data["can_change_host_audio_output"])

    def test_empty_devices_are_not_a_host_success(self):
        class EmptySD(FakeSD):
            def query_devices(self):
                return []
        data = inspect_audio_routing(EmptySD())
        self.assertTrue(data["available"])
        self.assertEqual(data["devices"], [])
        self.assertFalse(data["logic_audio_device_observed"])


if __name__ == "__main__":
    unittest.main()
