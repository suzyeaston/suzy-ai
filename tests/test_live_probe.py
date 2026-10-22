"""Offline regression tests for the live probe; no Focusrite or sounddevice required."""
import io
import struct
import unittest
import wave
from unittest.mock import patch

from suzy_ai.music.live import LiveSession
from suzy_ai.music.live_probe import (
    BLOCKSIZE, CHANNELS, FRAME_BYTES, RATE, DuplexBuffer, capture_levels, choose_listening_output,
    diagnostic_tone, performer_countdown, test_output, process, resolve_devices, response_pcm,
)


class LiveProbeTests(unittest.TestCase):
    def test_separate_input_output_device_routing(self):
        self.assertEqual(resolve_devices("0"), 0)
        self.assertEqual(resolve_devices(input_device="0", output_device="4"), (0, 4))
        self.assertEqual(resolve_devices(input_device="0", output_device=2), (0, 2))
        self.assertEqual(resolve_devices(input_device="0", output_device="2"), (0, 2))
        self.assertEqual(resolve_devices(input_device="Scarlett", output_device="MacBook"), ("Scarlett", "MacBook"))
        self.assertIsNone(resolve_devices())
        with self.assertRaises(ValueError):
            resolve_devices(input_device="0")
        with self.assertRaises(ValueError):
            resolve_devices(device="0", input_device="0", output_device="4")


    def test_output_selector_previews_until_performer_hears_it(self):
        class FakeDeviceList:
            @staticmethod
            def query_devices():
                return [
                    {"name": "Scarlett Solo USB", "max_output_channels": 2},
                    {"name": "External Microphone", "max_output_channels": 0},
                    {"name": "External Headphones", "max_output_channels": 2},
                    {"name": "MacBook Microphone", "max_output_channels": 0},
                    {"name": "MacBook Pro Speakers", "max_output_channels": 2},
                ]

        answers = iter(["9", "4", "n", "2", "yes"])
        messages, previewed = [], []
        chosen = choose_listening_output(
            FakeDeviceList(),
            read=lambda prompt: next(answers),
            announce=messages.append,
            preview=lambda sd, device: previewed.append(device),
        )
        self.assertEqual(chosen, 2)
        self.assertEqual(previewed, [4, 2])
        self.assertTrue(any("External Headphones" in s for s in messages))
        self.assertTrue(any("Not confirmed" in s for s in messages))

    def test_output_selector_does_not_capture_when_cancelled(self):
        class FakeDeviceList:
            @staticmethod
            def query_devices():
                return [{"name": "Headphones", "max_output_channels": 2}]

        with self.assertRaises(KeyboardInterrupt):
            choose_listening_output(FakeDeviceList(), read=lambda _: "q",
                                    announce=lambda _: None,
                                    preview=lambda *_: self.fail("should not play"))

    def test_output_selector_requires_stereo_output(self):
        class FakeDeviceList:
            @staticmethod
            def query_devices():
                return [{"name": "Mic", "max_output_channels": 0}]

        with self.assertRaisesRegex(ValueError, "No stereo output"):
            choose_listening_output(FakeDeviceList())

    def test_countdown_is_ready_before_capture(self):
        prompts, sleeps, lines = [], [], []

        def fake_read(message):
            prompts.append(message)
            return ""

        performer_countdown(3, 4.0, read=fake_read,
                            pause=sleeps.append,
                            announce=lambda message, **kwargs: lines.append(message))
        self.assertEqual(len(prompts), 1)
        self.assertIn("Press Return", prompts[0])
        self.assertEqual(sleeps, [1.0, 1.0, 1.0])
        self.assertEqual(lines[:3], ["  3...", "  2...", "  1..."])
        self.assertIn("RECORDING NOW", lines[-1])
        self.assertIn("4.0 seconds", lines[-1])
        with self.assertRaises(ValueError):
            performer_countdown(11, 4.0, read=fake_read)

    def test_levels_identify_input_channels_and_silence(self):
        pcm = struct.pack("<hh", 16384, 0) * 16
        levels = capture_levels(pcm)
        self.assertAlmostEqual(levels[0][0], 0.5)
        self.assertAlmostEqual(levels[0][1], 0.5)
        self.assertEqual(levels[1], (0.0, 0.0))
        self.assertEqual(capture_levels(bytes(4 * 100)), [(0.0, 0.0), (0.0, 0.0)])
        with self.assertRaises(ValueError):
            capture_levels(b"\0\0")

    def test_safe_output_tone_is_stereo_nonzero_and_faded(self):
        pcm = diagnostic_tone()
        self.assertEqual(len(pcm), round(0.75 * RATE) * FRAME_BYTES)
        channels = struct.unpack("<" + "h" * (len(pcm) // 2), pcm)
        self.assertEqual(channels[::2], channels[1::2])
        self.assertEqual(channels[0], 0)
        self.assertEqual(channels[-1], 0)
        self.assertGreater(max(abs(x) for x in channels), 500)
        self.assertLessEqual(max(abs(x) for x in channels), round(32767 * 0.06) + 1)
        for duration, gain in ((0.1, 0.06), (0.75, 0), (0.75, 0.5)):
            with self.assertRaises(ValueError):
                diagnostic_tone(duration, gain)

    def test_output_only_diagnostic_does_not_open_microphone(self):
        class FakeStream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def write(self, pcm):
                self.pcm = pcm

        class FakeAudio:
            def query_devices(self, device, direction):
                assert (device, direction) == (2, "output")
                return {"name": "External Headphones"}

            def RawOutputStream(self, **kwargs):
                assert kwargs["device"] == 2
                assert kwargs["channels"] == 2
                assert kwargs["samplerate"] == RATE
                return self.stream

        fake = FakeAudio()
        fake.stream = FakeStream()
        with patch("suzy_ai.music.live_probe.time.sleep"):
            test_output(fake, 2)
        self.assertEqual(len(fake.stream.pcm), round(0.75 * RATE) * FRAME_BYTES)

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
