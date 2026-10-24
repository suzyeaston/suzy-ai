"""QA for real recording A/B, honest source features and safe preview WAV."""
from array import array
import io
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

from suzy_ai.music.listening_lab import (
    arrangement_preview, compare, half_beat_energy, read_short_wav,
)
from suzy_ai.music.qwen_composer import (
    CompositionError, PROMPT, validate_accompaniment,
)


def make_wav(path, *, rate=48000, channels=1, seconds=4,
             pitch=220, gain=5000):
    buf=array("h")
    for i in range(rate*seconds):
        val=round(gain*math.sin(2*math.pi*pitch*i/rate))
        for c in range(channels):
            buf.append(val)
    if sys.byteorder!="little":buf.byteswap()
    with wave.open(str(path),"wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(buf.tobytes())


def mock_phrase():
    return {"status":"monophonic_candidate","duration_seconds":4,
            "bpm_supplied":90,"notes":[
                {"midi_note":60,"confidence":.99,"start_beats":0},
                {"midi_note":64,"confidence":.99,"start_beats":1},
                {"midi_note":67,"confidence":.99,"start_beats":2},
            ]}


class LabTests(unittest.TestCase):
    def test_real_pcm_wav_and_relative_beat_energy(self):
        with tempfile.TemporaryDirectory() as d:
            voice=Path(d)/"voice.wav"
            beat=Path(d)/"beat.wav"
            make_wav(voice,channels=1)
            make_wav(beat,channels=2)
            v=read_short_wav(voice)
            b=read_short_wav(beat)
            self.assertEqual((v["rate"],v["channels"],v["frames"]),(48000,1,192000))
            self.assertEqual(b["channels"],2)
            energy=half_beat_energy(b,90)
            self.assertEqual(len(energy),12)
            self.assertTrue(all(0<=e<=1 for e in energy))
            context=validate_accompaniment({"half_beat_energy":energy,"chord":"Am9"},6)
            self.assertEqual(context["chord_supplied"],"Am9")
            with self.assertRaises(ValueError):
                half_beat_energy(b,0)
            with self.assertRaises(CompositionError):
                validate_accompaniment({"half_beat_energy":[float("nan")]*12,"chord":None},6)

    def test_real_recordings_are_kept_in_both_ab_mixes(self):
        class MockComposer:
            def __init__(self): self.calls=[]
            def __call__(self,phrase,*,instruction,use_deep_research,accompaniment):
                self.calls.append((phrase,instruction,use_deep_research,accompaniment))
                pitch=65 if use_deep_research else 72
                return {"model":"mock_not_real_qwen",
                        "bpm_supplied":90,"duration_seconds":4.0,
                        "events":[{"start_beats":.5,"midi_note":pitch,
                                   "duration_beats":.5,"velocity":70}],
                        "references_offered":["baduizm-1997-call-space"] if use_deep_research else [],
                        "reference_used":"baduizm-1997-call-space" if use_deep_research else None}
        with tempfile.TemporaryDirectory() as d:
            voice,beat=Path(d)/"voice.wav",Path(d)/"beat.wav"
            make_wav(voice)
            make_wav(beat,pitch=110)
            out=Path(d)/"experiment"
            model=MockComposer()
            with patch("suzy_ai.music.listening_lab.extract_phrase",return_value=mock_phrase()):
                report=compare(voice,beat,bpm=90,chord="Am9",
                               query="Baduizm vocal space",out_dir=str(out),
                               composer=model)
            self.assertEqual(len(model.calls),2)
            self.assertFalse(model.calls[0][2])
            self.assertTrue(model.calls[1][2])
            self.assertEqual(model.calls[0][3],model.calls[1][3])
            self.assertEqual(model.calls[0][0],model.calls[1][0])
            self.assertTrue(report["not_proof_of_learning"])
            self.assertFalse(report["identical_note_events"])
            self.assertEqual(report["lead_notes_detected"],3)
            a=(out/"A_no_research.wav").read_bytes()
            b=(out/"B_with_research.wav").read_bytes()
            self.assertNotEqual(a,b)
            with wave.open(io.BytesIO(a),"rb") as f:
                self.assertEqual((f.getframerate(),f.getnframes(),f.getnchannels()),(48000,192000,2))
            self.assertIn('"identical_note_events": false',(out/"comparison.json").read_text())

    def test_alignment_mismatch_rejected_no_bad_mix(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"a.wav",Path(d)/"b.wav"
            make_wav(a,seconds=4)
            make_wav(b,seconds=3)
            with self.assertRaisesRegex(ValueError,"aligned"):
                compare(a,b,bpm=100,chord=None,query="jazz",
                        out_dir=str(Path(d)/"out"))

    def test_v2_prompt_no_two_note_template(self):
        self.assertNotIn('[[0.5,64,0.5,70],[1.5,62,0.5,64]]',PROMPT)
        self.assertIn("4-8 notes",PROMPT)
        self.assertIn("musical",PROMPT.lower())


if __name__=="__main__":
    unittest.main()
