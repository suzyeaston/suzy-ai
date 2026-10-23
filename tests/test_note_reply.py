"""Offline synthesis tests for a model-directed melodic reply.

No sounddevice, actual model, microphone, files or hardware required.
"""
from array import array
import math
import struct
import unittest

from suzy_ai.music.audio import describe
from suzy_ai.music.note_reply import NOTE_GESTURES, mix_note_reply, render_note_reply
from suzy_ai.music.live import LiveSession
from suzy_ai.music.live_probe import process, smoke_test_model


def singing_test_phrase(rate=48000, seconds=2.0, channels=2, side=0, amp=0.02):
    data = bytearray()
    for i in range(round(rate * seconds)):
        sample = round(32767 * amp * math.sin(2 * math.pi * 440 * i / rate))
        if channels == 2:
            data.extend(struct.pack("<hh", sample if side == 0 else 0,
                                    sample if side == 1 else 0))
        else:
            data.extend(struct.pack("<h", sample))
    return bytes(data)


class ModelNoteReplyTests(unittest.TestCase):
    def test_one_channel_scarlett_pitch_is_not_attenuated_before_analysis(self):
        for side in (0, 1):
            audio = singing_test_phrase(side=side)
            features = describe(audio, 48000, 2, 120)
            self.assertTrue(features['musical']['pitch_hints'])
            self.assertTrue(all(item['midi_note'] == 69
                                for item in features['musical']['pitch_hints']))

    def test_four_gestures_produce_different_new_note_answers(self):
        features = describe(singing_test_phrase(), 48000, 2, 120)
        starts = {}
        for gesture in NOTE_GESTURES:
            pcm, pitches = render_note_reply(features, gesture)
            self.assertEqual(len(pcm), 48000 * 2 * 4)
            self.assertTrue(pitches)
            self.assertTrue(all(48 <= p <= 84 for p in pitches))
            samples = array('h'); samples.frombytes(pcm)
            self.assertEqual(samples[::2], samples[1::2])
            self.assertLessEqual(max(map(abs, samples)), 2000)
            starts[gesture] = pitches[0]
        self.assertEqual(starts['answer-fifth'], 76)
        self.assertEqual(starts['answer-third'], 73)
        self.assertEqual(starts['answer-below'], 64)
        self.assertEqual(starts['answer-octave'], 81)

    def test_no_guessed_notes_on_low_confidence_or_no_pitch(self):
        features = describe(singing_test_phrase(), 48000, 2, 120)
        features['musical']['pitch_hints'] = []
        pcm, notes = render_note_reply(features, 'answer-fifth')
        self.assertEqual(notes, [])
        self.assertFalse(any(pcm))
        with self.assertRaises(ValueError):
            render_note_reply(features, 'unknown-model-answer')

    def test_bounded_mix_keeps_both_headphones_and_limits_peak(self):
        pcm = struct.pack("<hh", 24000, 24000) * 16
        mixed = mix_note_reply(pcm, pcm, source_gain=.5)
        self.assertEqual(len(mixed), len(pcm))
        self.assertEqual(struct.unpack("<hh", mixed[:4]), (16384, 16384))
        with self.assertRaises(ValueError):
            mix_note_reply(pcm, b"")
        with self.assertRaises(ValueError):
            mix_note_reply(pcm, pcm, source_gain=2)

    def test_note_provider_requires_actual_model_gesture(self):
        with self.assertRaisesRegex(ValueError, 'provider=model'):
            LiveSession().arm(dict(sample_rate=48000, channels=2, bpm=120,
                                   mode='evolve', provider='deterministic',
                                   response_style='notes'))
        audio = singing_test_phrase(seconds=.5)
        planner = lambda features, config: (
            {'slices': [{'index': i, 'gain': .8, 'reverse': False}
                        for i in range(len(features['slices']))]}, 'fake-model')
        session = LiveSession(planner=planner)
        with self.assertRaisesRegex(RuntimeError, 'valid note answer'):
            process(session, audio, bpm=120, mode='evolve',
                    provider='model', instruction='reply',
                    response_style='notes')

    def test_synthetic_note_model_smoke_uses_real_reply_manifest(self):
        def fake_planner(features, config):
            self.assertEqual(config['response_style'], 'notes')
            return (
                {'slices': [{'index': i, 'gain': .8, 'reverse': False}
                            for i in range(len(features['slices']))]},
                'fake-model', 'answer-fifth')
        manifest = smoke_test_model(planner=fake_planner, response_style='notes')
        self.assertEqual(manifest['provider'], 'model')
        self.assertEqual(manifest['reply_gesture'], 'answer-fifth')
        self.assertEqual(len(manifest['plan']['slices']), 8)


if __name__ == '__main__':
    unittest.main()
