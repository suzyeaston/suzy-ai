"""Offline characterization of the optional phrase-events probe."""
import math
import struct
import unittest
from suzy_ai.music.phrase import extract_phrase

RATE = 48000


def synthetic(segments, channels=1, side=0, rate=RATE):
    data = bytearray()
    for length, freq in segments:
        for i in range(round(length*rate)):
            sample = round(8500*math.sin(2*math.pi*freq*i/rate)) if freq else 0
            if channels == 1:
                data.extend(struct.pack('<h', sample))
            else:
                data.extend(struct.pack('<hh', sample if side == 0 else 0,
                                        sample if side == 1 else 0))
    return bytes(data)


class PhraseTests(unittest.TestCase):
    def test_three_notes_not_one_median_pitch(self):
        pcm = synthetic([(0.22,0),(0.40,261.626),(0.15,0),
                         (0.40,329.628),(0.15,0),(0.40,392.0),(0.22,0)])
        result = extract_phrase(pcm, RATE, 1, 120)
        self.assertEqual(result['status'], 'monophonic_candidate')
        notes = result['notes']
        self.assertEqual([n['midi_note'] for n in notes], [60,64,67])
        self.assertEqual(result['intervals'], [4,3])
        self.assertEqual(result['contour'], ['up','up'])
        self.assertTrue(result['rests'])
        self.assertTrue(all(n['confidence'] >= 0.84 for n in notes))
        self.assertAlmostEqual(notes[0]['start_beats'], notes[0]['start_seconds']*2, delta=.01)
        self.assertIsNone(result['key_detected'])

    def test_stereo_one_sided_scarlett(self):
        for side in (0, 1):
            result = extract_phrase(synthetic([(0.4,440),(0.4,349.228)],2,side),RATE,2,100)
            self.assertEqual([n['midi_note'] for n in result['notes']],[69,65])
            self.assertEqual(result['contour'], ['down'])

    def test_silence_and_bounded_input(self):
        silent = extract_phrase(bytes(RATE*2),RATE,1,120)
        self.assertEqual(silent['status'],'unvoiced')
        self.assertFalse(silent['notes'])
        for bad in (b'', b'\x00', b'\x00'* (RATE*8*2+2)):
            with self.assertRaises(ValueError): extract_phrase(bad,RATE,1,120)
        for rate,channels,bpm in [(44101,1,120),(RATE,3,120),(RATE,1,float('nan')),
                                  (RATE,1,0),(True,1,120),(RATE,True,120)]:
            with self.assertRaises(ValueError): extract_phrase(b'\x00'*4096,rate,channels,bpm)

    def test_rate_and_duration(self):
        pcm=synthetic([(0.75,220)],rate=44100)
        result=extract_phrase(pcm,44100,1,120)
        self.assertEqual([n['midi_note'] for n in result['notes']],[57])
        self.assertEqual(result['duration_seconds'],.75)

if __name__=='__main__':
    unittest.main()
