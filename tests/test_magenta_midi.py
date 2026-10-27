"""Hardware-free contract tests for the CoreMIDI steering bridge."""
import unittest

from suzy_ai.music.magenta_midi import MagentaMidiBridge, VIRTUAL_PORT


class FakeOut:
    def __init__(self, owner=None):
        self.owner = owner
        self.opened_index = None
        self.messages = []
        self.name = None
        self.closed = False

    def open_virtual_port(self, name):
        self.name = name

    def get_ports(self):
        return list(self.owner.output_ports) if self.owner else []

    def open_port(self, index):
        self.opened_index = index

    def send_message(self, message):
        self.messages.append(list(message))

    def close_port(self):
        self.closed = True


class FakeIn:
    def __init__(self, owner):
        self.owner = owner
        self.index = None
        self.callback = None
        self.closed = False

    def get_ports(self):
        return list(self.owner.ports)

    def ignore_types(self, **kwargs):
        self.ignored = kwargs

    def open_port(self, index):
        self.index = index

    def set_callback(self, callback):
        self.callback = callback

    def close_port(self):
        self.closed = True

    def emit(self, message):
        assert self.callback is not None
        self.callback((message, 0.0))


class FakeRtMidi:
    def __init__(self):
        self.ports = ["Keystation Mini 32 MK3", VIRTUAL_PORT]
        self.output_ports = ["MRT2 - Collider Input"]
        self.outputs = []
        self.inputs = []

    def MidiOut(self):
        result = FakeOut(self)
        self.outputs.append(result)
        return result

    def MidiIn(self):
        result = FakeIn(self)
        self.inputs.append(result)
        return result


class MagentaMidiTests(unittest.TestCase):
    def setUp(self):
        self.hw = FakeRtMidi()
        self.bridge = MagentaMidiBridge(self.hw)
        self.output = self.hw.outputs[0]

    def tearDown(self):
        self.bridge.close()

    def connect(self):
        self.bridge.connect("Keystation Mini 32 MK3")
        return self.bridge.source

    def test_virtual_source_and_strict_selection(self):
        self.assertEqual(self.output.name, VIRTUAL_PORT)
        self.assertEqual(self.bridge.inputs(), ["Keystation Mini 32 MK3"])
        for invalid in ("Keystation", VIRTUAL_PORT, "", 0):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.bridge.connect(invalid)
        self.assertIsNotNone(self.connect())
        self.assertEqual(self.bridge.status()["magenta_connection"], "not_observed")
        self.assertEqual(self.bridge.status()["ai_audio_muted"], "not_observed")

    def test_explicit_collider_direct_destination_duplicates_midi_to_native_sink(self):
        self.assertFalse(self.bridge.status()["collider_direct_ready"])
        self.bridge.connect_collider()
        self.assertTrue(self.bridge.status()["collider_direct_ready"])
        self.assertIn("MRT2 - Collider Input", self.bridge.status()["collider_direct_output"])
        direct = self.hw.outputs[-1]
        self.assertEqual(direct.opened_index, 0)
        self.bridge.test_chord()
        self.assertIn([0x90, 57, 48], direct.messages)
        self.assertIn([0x90, 57, 48], self.output.messages)
        self.bridge.disconnect_collider()
        self.assertTrue(direct.closed)
        self.assertFalse(self.bridge.status()["collider_direct_ready"])
        self.assertEqual(self.bridge.status()["magenta_connection"], "not_observed")
        self.assertEqual(self.bridge.status()["ai_audio_muted"], "not_observed")

    def test_collider_port_absent_and_ambiguous_fails_closed(self):
        self.hw.output_ports.clear()
        with self.assertRaisesRegex(ValueError, "not found"):
            self.bridge.connect_collider()
        self.hw.output_ports = ["MRT2 - Collider Input", "MRT2 - Collider Input duplicate"]
        with self.assertRaisesRegex(ValueError, "Multiple"):
            self.bridge.connect_collider()
        self.assertFalse(self.bridge.status()["collider_direct_ready"])

    def test_direct_note_off_velocity_zero_and_octave_move(self):
        source = self.connect()
        source.emit([0x90, 60, 92])
        self.assertEqual(self.output.messages[-1], [0x90, 60, 92])
        source.emit([0x90, 60, 0])
        self.assertEqual(self.output.messages[-1], [0x80, 60, 0])
        self.bridge.change_mode("high")
        source.emit([0x90, 60, 70])
        self.assertEqual(self.output.messages[-1], [0x90, 72, 70])
        self.bridge.change_mode("low")
        self.assertIn([0x80, 72, 0], self.output.messages)
        source.emit([0x90, 60, 64])
        self.assertEqual(self.output.messages[-1], [0x90, 48, 64])
        source.emit([0x80, 60, 0])
        self.assertEqual(self.output.messages[-1], [0x80, 48, 0])

    def test_gate_pauses_new_notes_and_releases_held(self):
        source = self.connect()
        source.emit([0x90, 64, 100])
        self.bridge.set_gate(False)
        self.assertIn([0x80, 64, 0], self.output.messages)
        before = len(self.output.messages)
        source.emit([0x90, 65, 100])
        self.assertEqual(len(self.output.messages), before)
        self.assertFalse(self.bridge.status()["gate_open"])
        with self.assertRaises(ValueError):
            self.bridge.test_chord()
        self.bridge.set_gate(True)
        source.emit([0x90, 65, 100])
        self.assertEqual(self.output.messages[-1], [0x90, 65, 100])

    def test_release_and_disconnect_never_pretend_audio_muted(self):
        source = self.connect()
        source.emit([0x90, 69, 96])
        released = self.bridge.release()
        self.assertEqual(released["held_notes"], 0)
        self.assertEqual(released["ai_audio_muted"], "not_observed")
        self.assertIn([0xB0, 123, 0], self.output.messages)
        self.bridge.disconnect()
        self.assertTrue(source.closed)
        self.assertIsNone(self.bridge.status()["input_name"])

    def test_test_chord_is_short_and_released(self):
        s = self.bridge.test_chord()
        self.assertEqual(s["held_notes"], 4)
        self.assertIn([0x90, 57, 48], self.output.messages)
        self.bridge._finish_test()
        self.assertEqual(self.bridge.status()["held_notes"], 0)
        self.assertIn([0x80, 57, 0], self.output.messages)
        self.bridge.release()

    def test_invalid_mode_does_not_change_playing_note(self):
        source = self.connect()
        source.emit([0x90, 60, 50])
        with self.assertRaises(ValueError):
            self.bridge.change_mode("answer")
        self.assertEqual(self.bridge.status()["held_notes"], 1)
        source.emit([0x80, 60, 0])
        self.assertEqual(self.bridge.status()["held_notes"], 0)

    def test_close_always_releases_and_closes_ports(self):
        source = self.connect()
        source.emit([0x90, 60, 65])
        self.bridge.close()
        self.assertTrue(source.closed)
        self.assertTrue(self.output.closed)
        self.assertIn([0x80, 60, 0], self.output.messages)
        self.bridge.close()


if __name__ == "__main__":
    unittest.main()
