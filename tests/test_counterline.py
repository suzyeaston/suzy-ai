"""Offline validation: new contour-derived notes, no model or audio device."""
from array import array
import io
import unittest
import wave

from suzy_ai.music.counterline import compose_counterline, render_counterline, audition_wav
from suzy_ai.music.phrase import extract_phrase
from test_phrase import synthetic


def source():
    pcm=synthetic([(0.22,0),(.4,261.626),(.15,0),(.4,329.628),(.15,0),(.4,392),(.22,0)])
    return extract_phrase(pcm,48000,1,120)


class CounterlineTests(unittest.TestCase):
    def test_counterline_has_own_contour_and_rhythm(self):
        phrase=source()
        plan=compose_counterline(phrase)
        self.assertEqual(plan['status'],'composed')
        self.assertEqual(len(plan['events']),3)
        self.assertEqual(plan,compose_counterline(phrase))
        pitches=[n['midi_note'] for n in plan['events']]
        self.assertEqual(pitches,[67,63,60])
        self.assertEqual([n['midi_note'] for n in phrase['notes']],[60,64,67])
        self.assertTrue(all(n['start_beats'] >= .5 for n in plan['events']))
        self.assertTrue(all(n['velocity'] <= 90 for n in plan['events']))

    def test_optional_harmony_is_explicit_and_changes_pitch(self):
        plan=compose_counterline(source(),harmony={'root_pc':0,'quality':'major'})
        self.assertEqual(plan['harmony_source'],'performer_supplied')
        self.assertTrue(all(n['midi_note']%12 in (0,4,7) for n in plan['events']))
        with self.assertRaises(ValueError): compose_counterline(source(),harmony={'root_pc':12,'quality':'minor'})
        with self.assertRaises(ValueError): compose_counterline(source(),harmony={'root_pc':0,'quality':'dominant'})
        with self.assertRaises(ValueError): compose_counterline(source(),harmony={'root_pc':0,'quality':'major','other':'x'})

    def test_silence_and_uncertain_pitch_never_invent_music(self):
        silent=extract_phrase(bytes(48000*2),48000,1,120)
        self.assertEqual(compose_counterline(silent)['events'],[])
        s=source()
        for note in s['notes']: note['confidence']=.5
        self.assertEqual(compose_counterline(s)['events'],[])

    def test_stereo_wav_bounded_nonempty_and_malformed_input_rejected(self):
        plan=compose_counterline(source())
        pcm=render_counterline(plan)
        samples=array('h');samples.frombytes(pcm)
        self.assertEqual(samples[::2],samples[1::2])
        self.assertTrue(any(samples))
        self.assertLess(max(map(abs,samples)),3000)
        with wave.open(io.BytesIO(audition_wav(plan))) as wav:
            self.assertEqual((wav.getframerate(),wav.getnchannels(),wav.getnframes()),(48000,2,round(48000*plan['duration_seconds'])))
        for bad in (None,{'start_beats':float('nan'),'duration_beats':1,'midi_note':60,'velocity':70},
                    {'start_beats':0,'duration_beats':1,'midi_note':True,'velocity':70}):
            mutated=dict(plan,events=[bad])
            with self.assertRaises((ValueError,TypeError)): render_counterline(mutated)

    def test_sparse_below_and_oblique_controls(self):
        phrase=source()
        below=compose_counterline(phrase,register='below',density='sparse')
        self.assertLess(len(below['events']),len(compose_counterline(phrase)['events']))
        self.assertTrue(all(48 <= n['midi_note'] <= 84 for n in below['events']))
        oblique=compose_counterline(phrase,motion='oblique')
        self.assertEqual(len(set(n['midi_note'] for n in oblique['events'])),1)
        self.assertTrue(any(render_counterline(oblique,rate=44100)))

    def test_invalid_phrase_and_controls(self):
        for kwargs in ({'register':'infinity'},{'motion':'fake'},{'density':'max'}):
            with self.assertRaises(ValueError): compose_counterline(source(),**kwargs)
        source_notes=source()
        reversed_notes=dict(source_notes,notes=list(reversed(source_notes['notes'])))
        for variant in [reversed_notes, dict(status='unvoiced',bpm_supplied=120,duration_seconds=0,notes=[]),
                        dict(status='monophonic_candidate',bpm_supplied=120,duration_seconds=4,notes=[{'midi_note':True,'confidence':1,'start_beats':0,'duration_beats':1}])]:
            with self.assertRaises(ValueError): compose_counterline(variant)


if __name__=='__main__':
    unittest.main()
