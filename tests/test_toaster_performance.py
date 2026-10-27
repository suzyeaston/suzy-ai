"""Hardware-free tests for live TOASTER MIDI chord pads and rhythm."""
import time
import unittest
from suzy_ai.music.toaster_performance import ToasterPerformance
from suzy_ai.music.magenta_midi import MagentaMidiBridge
from tests.test_magenta_midi import FakeRtMidi


class ToasterPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.hw = FakeRtMidi()
        self.bridge = MagentaMidiBridge(self.hw)
        self.perf = ToasterPerformance(self.bridge)
        self.out = self.hw.outputs[0]

    def tearDown(self):
        self.perf.close()
        self.bridge.close()

    def test_four_computer_pads_work_without_any_keystation_input(self):
        self.assertIsNone(self.bridge.source)
        self.assertEqual(self.perf.chord(0)["chord_index"], 0)
        self.assertIn([0x90, 54, 56], self.out.messages)
        self.perf.chord(1)
        self.assertIn([0x80, 54, 0], self.out.messages)
        self.assertIn([0x90, 55, 56], self.out.messages)
        self.perf.scene_change("fishes")
        self.assertIn([0x80, 55, 0], self.out.messages)
        self.assertEqual(self.perf.chord(0)["chords"][0], "Em7")
        self.assertIn([0x90, 52, 56], self.out.messages)
        self.assertFalse(self.perf.status()["magenta_audio_confirmed"])

    def test_strict_chord_scene_tempo_and_groove_validation(self):
        for i in (True, "2", 4, -1, 1.0):
            with self.subTest(index=i), self.assertRaises(ValueError):
                self.perf.chord(i)
        for scene in ("other", "", 0):
            with self.subTest(scene=scene), self.assertRaises(ValueError):
                self.perf.scene_change(scene)
        for invalid in [(105.0,"float",50),(192,"float",50),(90,"swing",30),(90,"pulse",101),(90,"pulse",True)]:
            with self.subTest(args=invalid), self.assertRaises(ValueError):
                self.perf.settings(bpm=invalid[0],rhythm=invalid[1],intensity=invalid[2])

    def test_groove_start_stop_and_no_stuck_midi(self):
        with self.assertRaises(ValueError):
            self.perf.start()
        self.perf.chord(2)
        self.perf.settings(bpm=190,rhythm="arpeggio",intensity=35)
        self.assertTrue(self.perf.start()["running"])
        time.sleep(.18)
        self.assertTrue(any(msg[0]==0x90 and msg[1] >= 72 for msg in self.out.messages),
                        "groove voice uses first MIDI channel and upper octave")
        self.assertEqual(self.perf.status()["midi_channel"], 1)
        self.assertGreater(self.perf.status()["step"],0)
        self.perf.stop()
        self.assertFalse(self.perf.status()["running"])
        self.assertEqual(self.perf.chord_notes,())
        self.assertIsNone(self.perf.groove_note)
        self.assertTrue(any(msg[0]==0x80 for msg in self.out.messages))
        self.assertEqual(self.perf.status()["clock"], "independent_monotonic_not_logic_synced")

    def test_gate_and_closed_bridge_refuse_new_notes(self):
        self.bridge.set_gate(False)
        with self.assertRaises(ValueError):
            self.perf.chord(0)
        self.bridge.set_gate(True)
        self.perf.chord(0)
        self.bridge.close()
        with self.assertRaises(ValueError):
            self.perf.chord(1)


if __name__ == "__main__":
    unittest.main()
