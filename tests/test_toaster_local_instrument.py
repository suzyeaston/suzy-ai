"""Static contract for locally audible, human-led TOASTER chord pads.

This verifies no extra model or package is needed, and distinguishes true
browser synthesis from CoreMIDI symbolic conditioning. Hardware playback still
needs the performer's Mac/headphones.
"""
from pathlib import Path
import unittest

PAGE = Path(__file__).resolve().parents[1] / "suzy_ai/music/toaster_live.html"


class ToasterLocalInstrumentTests(unittest.TestCase):
    def test_local_audio_is_explicit_click_to_start_and_reachable_from_four_pads(self):
        html = PAGE.read_text(encoding="utf8")
        self.assertIn('id="localAudio"', html)
        self.assertIn('id="localMute"', html)
        self.assertIn('id="localReverb"', html)
        self.assertIn('id="localVoice"', html)
        self.assertIn('id="localGain"', html)
        self.assertIn('if(localEnabled)playLocalChord(i).catch(error);', html)
        self.assertIn('localEnabled=false', html)
        self.assertIn('async function startLocal()', html)
        self.assertIn('async function playLocalChord(index)', html)
        self.assertIn('ctx.createOscillator()', html)
        self.assertIn('ctx.createConvolver()', html)
        self.assertIn('window.AudioContext||window.webkitAudioContext', html)
        self.assertIn('function stopVoices()', html)

    def test_original_harmonies_and_no_fake_magenta_or_audio_claims(self):
        html = PAGE.read_text(encoding="utf8")
        self.assertIn('pyramid:[[54,58,61,66]', html)
        self.assertIn('fishes:[[52,55,59,62]', html)
        self.assertIn('MODEL AND MIDI NOT REQUIRED FOR SOUND', html)
        self.assertIn('The Magenta / Collider volume must be controlled in its own app', html)
        self.assertNotIn('MRT2 AUDIO CONNECTED', html)
        self.assertNotIn('<script src=', html)
        self.assertNotIn('tone.js', html.lower())
        self.assertNotIn('https://cdn.', html)


if __name__ == "__main__":
    unittest.main()
