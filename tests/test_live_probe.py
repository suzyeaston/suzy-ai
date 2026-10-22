"""Offline regression tests for the live probe; no Focusrite or sounddevice required."""
import io
import struct
import unittest
import wave

from suzy_ai.music.live import LiveSession
from suzy_ai.music.live_probe import (
    BLOCKSIZE, CHANNELS, FRAME_BYTES, RATE, DuplexBuffer, process, resolve_devices, response_pcm,
)


class LiveProbeTests(unittest.TestCase):
    def test_separate_input_output_device_routing(self):
        self.assertEqual(resolve_devices("0"), 0)
        self.assertEqual(resolve_devices(input_device="0", output_device="4"), (0, 4))
        self.assertEqual(resolve_devices(input_device="0", output_device="2"), (0, 2))
        self.assertEqual(resolve_devices(input_device="Scarlett", output_device="MacBook"), ("Scarlett", "MacBook"))
        self.assertIsNone(resolve_devices())
        with self.assertRaises(ValueError):
            resolve_devices(input_device="0")
        with self.assertRaises(ValueError):
            resolve_devices(device="0", input_device="0", output_device="4")


    def test_capture_exact_length_and_silent_output(self):
        audio = DuplexBuffer(BLOCKSIZE + 13)
        audio.arm()
        microphone = struct.pack("<hh", 3200, -1800) * BLOCKSIZE
        output = bytearray(len(microphone))
        audio.callback(microphone, output, BLOCKSIZE)
        self.assertEqual(bytes(output), bytes(len(output)))
        self.assertTrue(audio.recording)
        audio.callback(microphone, output, BLOCKSIZE)
        self.assertFalse(audio.recording)
        self.assertEqual(len(audio.captured()), (BLOCKSIZE + 13) * FRAME_BYTES)
        self.assertEqual(audio.captured()[-FRAME_BYTES:], struct.pack("<hh", 3200, -1800))
        # Once captured, the stream must not overwrite the immutable phrase.
        prior = audio.captured()
        audio.callback(bytes(len(microphone)), output, BLOCKSIZE)
        self.assertEqual(audio.captured(), prior)

    def test_response_playback_and_idle_silence(self):
        audio = DuplexBuffer(200)
        payload = struct.pack("<hh", 2000, -2000) * (BLOCKSIZE + 1)
        audio.play(payload)
        output = bytearray(BLOCKSIZE * FRAME_BYTES)
        audio.callback(bytes(len(output)), output, BLOCKSIZE)
        self.assertEqual(bytes(output), payload[:len(output)])
        self.assertTrue(audio.playing)
        audio.callback(bytes(len(output)), output, BLOCKSIZE)
        self.assertFalse(audio.playing)
        self.assertEqual(bytes(output[:FRAME_BYTES]), payload[-FRAME_BYTES:])
        self.assertEqual(bytes(output[FRAME_BYTES:]), bytes(len(output) - FRAME_BYTES))
        audio.callback(bytes(len(output)), output, BLOCKSIZE)
        self.assertEqual(bytes(output), bytes(len(output)))

    def test_cannot_arm_during_playback(self):
        audio = DuplexBuffer(100)
        audio.play(struct.pack("<hh", 100, 100))
        with self.assertRaises(RuntimeError):
            audio.arm()
        with self.assertRaises(ValueError):
            audio.play(b"\x01")
        with self.assertRaises(RuntimeError):
            audio.captured()

    def test_pcm_wav_playback_gain_without_files(self):
        frames = struct.pack("<hh", 12000, -8000) * 64
        stream = io.BytesIO()
        with wave.open(stream, "wb") as wav:
            wav.setframerate(RATE)
            wav.setnchannels(CHANNELS)
            wav.setsampwidth(2)
            wav.writeframes(frames)
        volume = response_pcm(stream.getvalue(), 0.25)
        self.assertEqual(struct.unpack("<hh", volume[:FRAME_BYTES]), (3000, -2000))
        self.assertEqual(len(volume), len(frames))
        with self.assertRaises(ValueError):
            response_pcm(self._mono_wav(), 0.5)

    @staticmethod
    def _mono_wav():
        stream = io.BytesIO()
        with wave.open(stream, "wb") as wav:
            wav.setframerate(RATE)
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.writeframes(struct.pack("<h", 500))
        return stream.getvalue()

    def test_backend_direct_round_trip_without_export(self):
        session = LiveSession()
        pcm = struct.pack("<hh", 9000, -7000) * (RATE // 2)
        cid, wav_bytes, metadata = process(
            session, pcm, bpm=120, mode="evolve",
            provider="deterministic", instruction="QA phrase")
        self.assertEqual(metadata["provider"], "deterministic")
        self.assertEqual(metadata["mode"], "evolve")
        self.assertEqual(session.status()["state"], "auditioning")
        self.assertEqual(len(response_pcm(wav_bytes, 0.3)), len(pcm))
        session.action(cid, "stop-audition")
        session.action(cid, "discard")
        self.assertEqual(session.status()["state"], "discarded")

    def test_failed_model_is_not_relabelled_as_deterministic(self):
        session = LiveSession(planner=lambda *_: ({"slices": []}, "broken"))
        pcm = struct.pack("<hh", 9000, -7000) * (RATE // 2)
        with self.assertRaisesRegex(RuntimeError, "response failed"):
            process(session, pcm, bpm=120, mode="evolve", provider="model",
                    instruction="QA failure")
        self.assertEqual(session.status()["state"], "discarded")


if __name__ == "__main__":
    unittest.main()
