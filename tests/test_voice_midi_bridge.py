"""No-interface unit QA for real-time voice-to-MIDI steering of local music AI."""
from array import array
import math
import sys
import unittest

from suzy_ai.music.voice_midi_bridge import (
    NoteGate, choose_device, choose_midi_port, estimated_pitch, WINDOW, RATE
)


class VoiceMidiBridgeTests(unittest.TestCase):
    def test_note_on_requires_stable_pitch_and_note_off_after_silence(self):
        gate=NoteGate(channel=1,stable_frames=2,silent_frames=3)
        self.assertEqual(gate.observe(60,.93,.1),[])
        self.assertEqual(gate.observe(60,.93,.1),[[0x90,60,65]])
        self.assertEqual(gate.observe(60,.95,.2),[])
        self.assertEqual(gate.observe(None,0,0),[])
        self.assertEqual(gate.observe(None,0,0),[])
        self.assertEqual(gate.observe(None,0,0),[[0x80,60,0]])
        self.assertEqual(gate.panic(),[[0xB0,123,0],[0xB0,120,0]])

    def test_pitch_change_always_releases_old_note_first(self):
        gate=NoteGate(transpose=-12,stable_frames=2)
        gate.observe(72,.99,.1)
        self.assertEqual(gate.observe(72,.99,.1),[[0x90,60,65]])
        self.assertEqual(gate.observe(75,.99,.1),[])
        self.assertEqual(gate.observe(75,.99,.1),
                         [[0x80,60,0],[0x90,63,65]])
        self.assertEqual(gate.panic(),
                         [[0x80,63,0],[0xB0,123,0],[0xB0,120,0]])

    def test_quiet_low_confidence_and_corrupt_input_never_emit_notes(self):
        gate=NoteGate()
        for pitch,conf,rms in [(60,.1,.5),(60,.99,.001),(60,float("nan"),.1),
                               (70,.99,float("inf")),(100,.99,.5)]:
            with self.subTest(pitch=pitch):
                self.assertEqual(gate.observe(pitch,conf,rms),[])
        self.assertIsNone(gate.active)

    def test_device_selection_is_explicit_and_refuses_ambiguity(self):
        inputs=[
            {"name":"Scarlett Solo USB","max_input_channels":2},
            {"name":"MacBook Microphone","max_input_channels":1},
            {"name":"Scarlett 2i2","max_input_channels":2},
            {"name":"Mac output","max_input_channels":0},
        ]
        self.assertEqual(choose_device(inputs,"Scarlett Solo","device"),0)
        self.assertEqual(choose_device(inputs,"1","device"),1)
        with self.assertRaises(ValueError):
            choose_device(inputs,"Scarlett","device")
        with self.assertRaises(ValueError):
            choose_device(inputs,"3","device")
        ports=["IAC Driver Bus 1","Magenta RT Input","Other MIDI Device"]
        self.assertEqual(choose_midi_port(ports,"Magenta RT Input"),1)
        self.assertEqual(choose_midi_port(ports,"0"),0)
        with self.assertRaises(ValueError):
            choose_midi_port(ports,"unknown")

    def test_pitch_estimation_needs_valid_dry_mono_pcm(self):
        buf=array("h",[0])*WINDOW
        # A clean unprocessed A4; the estimator is a 45ms approximation.
        for i in range(WINDOW):
            buf[i]=int(13000*math.sin(2*math.pi*440*i/RATE))
        if sys.byteorder!="little":
            buf.byteswap()
        pitch,confidence,rms=estimated_pitch(buf.tobytes(),channels=1,mic_channel=1)
        self.assertIsInstance(pitch,int)
        self.assertLessEqual(abs(pitch-69),1)
        self.assertGreaterEqual(confidence,.84)
        self.assertGreater(rms,.012)
        with self.assertRaises(ValueError):
            estimated_pitch(b"bad",channels=2,mic_channel=2)

    def test_invalid_gate_config_fails_before_hardware(self):
        for values in ({"channel":0},{"channel":17},{"transpose":-25},
                       {"stable_frames":0},{"silent_frames":0},{"min_confidence":.2}):
            with self.subTest(values=values),self.assertRaises(ValueError):
                NoteGate(**values)


if __name__=="__main__":
    unittest.main()
