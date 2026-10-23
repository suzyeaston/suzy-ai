"""Audio-sampled vocal reply QA; no microphone, web or real model needed."""
import http.client
import io
import json
import math
import struct
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from suzy_ai.music.audio import describe
from suzy_ai.music.live import LiveSession
from suzy_ai.music.planner import CorePlanner, ModelPlanningError
from suzy_ai.music.vocal_reply import VOCAL_GESTURES, render_vocal_layer
from suzy_ai.music.live_probe import (
    route_output_channels, smoke_test_model, process, vocal_audition_buffers,
    capture_levels, DuplexBuffer, RATE, BLOCKSIZE, FRAME_BYTES,
)


def hummed_phrase(frames=48000 * 2, rate=48000):
    """One-channel 440 Hz singer in the left Scarlett input."""
    return b"".join(struct.pack("<hh",
                   round(8000 * math.sin(2 * math.pi * 440 * i / rate)), 0)
                   for i in range(frames))


class VocalReplyTests(unittest.TestCase):
    def test_vocal_gestures_keep_real_recorded_waveform_at_original_duration(self):
        voice, _ = route_output_channels(hummed_phrase(), "mono-center")
        features = describe(voice, 48000, 2, 120)
        outputs = {}
        for gesture in VOCAL_GESTURES:
            result = render_vocal_layer(voice, features, gesture)
            self.assertEqual(len(result), len(voice))
            self.assertNotEqual(result, voice)
            self.assertTrue(any(result))
            self.assertEqual(len(result) % 4, 0)
            self.assertEqual(result[0:4], bytes(4))
            outputs[gesture] = result
        self.assertEqual(len(set(outputs.values())), 4)
        # Different time layout, same actual vocal source sample values.
        # A canon starts AFTER the first beat (no source phrase at time 0).
        canon = outputs["vocal-canon"]
        self.assertEqual(canon[:48000 * 2], bytes(48000 * 2))
        echo = outputs["vocal-echo"]
        self.assertEqual(echo[:48000 * 4], bytes(48000 * 4))

    def test_isolated_audio_vs_original_vs_duet_use_same_vocal_layer(self):
        raw = hummed_phrase()
        centered, _ = route_output_channels(raw, "mono-center")
        features = describe(raw, 48000, 2, 120)
        # Simulate the existing source renderer's conservative gain.
        response = bytes(centered)
        original, layer, duet = (
            vocal_audition_buffers(raw, response, features, "vocal-canon")[name]
            for name in ("original", "layer", "duet"))
        self.assertEqual(len(original), len(layer))
        self.assertEqual(len(duet), len(raw))
        self.assertEqual(layer[:48000 * 2], bytes(48000 * 2))
        self.assertTrue(any(layer[48000 * 2:]))
        self.assertNotEqual(original, layer)
        self.assertNotEqual(duet, original)
        self.assertNotEqual(duet, layer)
        levels = capture_levels(layer)
        self.assertGreater(levels[0][0], 0.01)
        self.assertEqual(levels[0], levels[1])
        # Before the canon delay, the mixed output contains only the
        # attenuated original. Afterward, the actual delayed voice enters.
        self.assertEqual(original[:48000 * 2], duet[:48000 * 2])
        self.assertNotEqual(original[48000 * 2:], duet[48000 * 2:])

    def test_same_capture_can_audition_all_three_outputs_sequentially(self):
        raw = hummed_phrase(frames=48000)
        features = describe(raw, 48000, 2, 120)
        centered, _ = route_output_channels(raw, "mono-center")
        parts = vocal_audition_buffers(raw, centered, features, "vocal-stutter")
        duplex = DuplexBuffer(RATE)
        for name, repeat_count in (("original", 1), ("layer", 1), ("duet", 4)):
            audio = parts[name]
            duplex.play(audio, repeats=repeat_count)
            block = bytearray(BLOCKSIZE * FRAME_BYTES)
            copied = 0
            while duplex.playing:
                duplex.callback(bytes(len(block)), block, BLOCKSIZE)
                copied = duplex.played
            self.assertEqual(copied, len(audio) * repeat_count)
        self.assertEqual(duplex.audio_flags, 0)

    def test_vocal_comparison_rejects_invalid_frame_sizes(self):
        raw = hummed_phrase()
        features = describe(raw, 48000, 2, 120)
        with self.assertRaises(ValueError):
            vocal_audition_buffers(raw, raw[:-4], features, "vocal-canon")

    def test_rejects_unapproved_gestures_or_mismatched_pcm(self):
        voice, _ = route_output_channels(hummed_phrase(), "mono-center")
        features = describe(voice, 48000, 2, 120)
        for gesture in ("generate-magic-voice", "answer-fifth", None):
            with self.assertRaises(ValueError):
                render_vocal_layer(voice, features, gesture)
        with self.assertRaises(ValueError):
            render_vocal_layer(voice[:-4], features, "vocal-canon")

    def test_requires_actual_model_decision_for_vocal_reply(self):
        config = dict(sample_rate=48000, channels=2, bpm=120,
                      mode="evolve", provider="deterministic",
                      response_style="vocal")
        with self.assertRaisesRegex(ValueError, "provider=model"):
            LiveSession().arm(config)
        def bad_planner(features, config):
            return {"slices": [
                {"index": i, "gain": .8, "reverse": False}
                for i in range(len(features["slices"]))]}, "fake"
        session = LiveSession(planner=bad_planner)
        with self.assertRaisesRegex(RuntimeError, "valid vocal response"):
            process(session, hummed_phrase(frames=24000), bpm=120,
                    mode="evolve", provider="model", instruction="real voice",
                    response_style="vocal")

    def test_model_smoke_works_without_mic_and_tracks_vocal_gesture(self):
        def planner(features, config):
            self.assertEqual(config["response_style"], "vocal")
            return ({"slices": [
                {"index": i, "gain": .8, "reverse": False}
                for i in range(len(features["slices"]))]},
                "fake-Qwen", "vocal-canon")
        result = smoke_test_model(planner=planner, response_style="vocal")
        self.assertEqual(result["provider"], "model")
        self.assertEqual(result["reply_gesture"], "vocal-canon")

    def test_real_planner_decodes_compact_vocal_choice_from_fake_core(self):
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append(data)
                resp = json.dumps({
                    "message": {"role": "assistant",
                                "content": json.dumps({"pattern": "vocal-stutter"})},
                    "model": "fake-model",
                }).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            planner = CorePlanner(f"http://127.0.0.1:{server.server_address[1]}/v1")
            voice = hummed_phrase()
            features = describe(voice, 48000, 2, 120)
            plan, model, gesture = planner(features, {
                "mode": "evolve", "instruction": "respond with my voice",
                "response_style": "vocal",
            })
            self.assertEqual(model, "fake-model")
            self.assertEqual(gesture, "vocal-stutter")
            self.assertEqual(len(plan["slices"]), 4)
            self.assertFalse(seen[0]["use_memory"])
            self.assertEqual(seen[0]["history"], [])
            self.assertIn("actual recorded voice", seen[0]["message"].lower())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
