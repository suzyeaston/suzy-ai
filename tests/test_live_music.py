import http.client
import io
import json
import math
import struct
import threading
import time
import unittest
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from suzy_ai.music.audio import describe, render, deterministic_plan, validate_plan
from suzy_ai.music.live import LiveSession, Conflict
from suzy_ai.music.planner import CorePlanner
from suzy_ai.music.server import make_server


def phrase(seconds=1, channels=1):
    # Four distinct musical pitches, with alternating dynamics.
    return b''.join(struct.pack('<h', int(9000 * (1 if (i // 12000) % 2 else 0.6)
                      * math.sin(2 * math.pi * (220 + 55 * (i // 12000)) * i / 48000))) * channels
                    for i in range(round(seconds * 48000)))


def config(**kwargs):
    return dict(sample_rate=48000, channels=1, bpm=120, mode='mirror', **kwargs)


def capture(session, pcm=None, **kwargs):
    pcm = phrase() if pcm is None else pcm
    state = session.arm(config(**kwargs))
    for sequence, offset in enumerate(range(0, len(pcm), 16384)):
        session.append(state['id'], sequence, pcm[offset:offset+16384])
    return state['id']


def wait(session):
    deadline = time.monotonic() + 3
    while session.status()['busy'] and time.monotonic() < deadline:
        time.sleep(0.005)
    if session.status()['busy']:
        raise AssertionError('worker failed to exit')
    return session.status()


class LiveMusicTests(unittest.TestCase):
    def test_source_audio_round_trip_and_approval_gate(self):
        session = LiveSession()
        capture_id = capture(session)
        with self.assertRaises(Conflict):
            session.audio(capture_id)
        session.finish(capture_id)
        status = wait(session)
        self.assertEqual(status['state'], 'ready')
        self.assertEqual(status['response']['provider'], 'deterministic')
        self.assertIsNone(status['response']['model'])
        with self.assertRaises(Conflict):
            session.audio(capture_id)
        session.action(capture_id, 'audition')
        with wave.open(io.BytesIO(session.audio(capture_id))) as wav:
            self.assertEqual((wav.getframerate(), wav.getnchannels(), wav.getnframes()), (48000, 1, 48000))
            samples = struct.unpack('<48000h', wav.readframes(48000))
            self.assertLessEqual(max(map(abs, samples)), 23198)
            self.assertEqual(samples[0], 0)
            self.assertNotEqual(sum(map(abs, samples)), 0)
        session.action(capture_id, 'stop-audition')
        session.action(capture_id, 'accept')
        self.assertTrue(session.audio(capture_id))
        session.action(capture_id, 'discard')
        with self.assertRaises(Conflict):
            session.audio(capture_id)

    def test_discard_during_inference_drops_late_result_and_prevents_queue(self):
        entered, release = threading.Event(), threading.Event()
        def planner(features, cfg):
            entered.set()
            release.wait(2)
            return deterministic_plan('mirror', len(features['slices'])), 'fake-model'
        session = LiveSession(planner)
        capture_id = capture(session, provider='model')
        started = time.monotonic()
        session.finish(capture_id)
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertTrue(entered.wait(1))
        session.action(capture_id, 'discard')
        with self.assertRaises(Conflict):
            session.arm(config())
        release.set()
        self.assertEqual(wait(session)['state'], 'discarded')
        self.assertIsNone(session.status()['response'])
        new_id = session.arm(config())['id']
        self.assertNotEqual(new_id, capture_id)
        with self.assertRaises(Conflict):
            session.append(capture_id, 0, b'\x00\x00')

    def test_no_silent_ai_fallback(self):
        for plan in ({'slices': []}, {'slices': [{'index': 0, 'gain': float('nan'), 'reverse': False}]}):
            session = LiveSession(lambda *args: (plan, 'fake-model'))
            capture_id = capture(session, provider='model')
            session.finish(capture_id)
            self.assertEqual(wait(session)['state'], 'failed')
            self.assertIsNone(session.status()['response'])

    def test_model_decisions_change_source_audio(self):
        def planner(features, cfg):
            plan = deterministic_plan('mirror', len(features['slices']))
            for item in plan['slices']:
                item['reverse'] = True
            return plan, 'test-only-model'
        results = []
        for provider in ('model', 'deterministic'):
            session = LiveSession(planner)
            cid = capture(session, provider=provider)
            session.finish(cid)
            self.assertEqual(wait(session)['state'], 'ready')
            session.action(cid, 'accept')
            results.append(session.audio(cid))
        self.assertNotEqual(*results)

    def test_chunk_sequence_alignment_and_capture_limit(self):
        session = LiveSession()
        cid = session.arm(config())['id']
        for sequence, data, error in ((1, b'\0\0', Conflict), (0, b'\0', ValueError), (0, bytes(65538), ValueError)):
            with self.assertRaises(error):
                session.append(cid, sequence, data)
        maximum = 48000 * 8 * 2
        for sequence, offset in enumerate(range(0, maximum, 65536)):
            session.append(cid, sequence, bytes(min(65536, maximum-offset)))
        with self.assertRaises(ValueError):
            session.append(cid, sequence+1, b'\0\0')
        self.assertEqual(session.status()['captured_bytes'], maximum)

    def test_invalid_config_and_silence(self):
        for key, value in (('sample_rate', True), ('channels', 3), ('bpm', float('nan')), ('mode', 'other'), ('provider', 'remote')):
            cfg = config()
            cfg[key] = value
            with self.assertRaises(ValueError):
                LiveSession().arm(cfg)
        session = LiveSession()
        cid = capture(session, bytes(48000))
        session.finish(cid)
        self.assertEqual(wait(session)['state'], 'failed')

    def test_deterministic_modes_stereo_duration_and_peak(self):
        pcm = phrase(channels=2)
        features = describe(pcm, 48000, 2, 120)
        outputs = []
        for mode in ('mirror', 'augment', 'evolve'):
            plan = deterministic_plan(mode, len(features['slices']))
            output = render(pcm, features, plan, mode)
            self.assertEqual(output, render(pcm, features, plan, mode))
            outputs.append(output)
            with wave.open(io.BytesIO(output)) as wav:
                self.assertEqual((wav.getnframes(), wav.getnchannels()), (48000, 2))
        self.assertEqual(len(set(outputs)), 3)

    def test_malicious_plan_rejected(self):
        for field, value in (('index', -1), ('index', True), ('gain', float('inf')), ('gain', True), ('reverse', 'yes')):
            plan = deterministic_plan('mirror', 1)
            plan['slices'][0][field] = value
            with self.assertRaises(ValueError):
                validate_plan(plan, 1)


class LiveHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, data=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=2)
        conn.request(method, path, data, headers or {})
        response = conn.getresponse()
        result = response.status, response.read()
        conn.close()
        return result

    def test_controller_lifecycle_over_http(self):
        code, body = self.request('POST', '/v1/live/capture', json.dumps(config()), {'Content-Type': 'application/json'})
        self.assertEqual(code, 201)
        cid = json.loads(body)['id']
        pcm = phrase(0.25)
        code, _ = self.request('POST', f'/v1/live/{cid}/chunks/0', pcm, {'Content-Type': 'application/octet-stream'})
        self.assertEqual(code, 200)
        code, _ = self.request('POST', f'/v1/live/{cid}/finish', '{}', {'Content-Type': 'application/json'})
        self.assertEqual(code, 202)
        wait(self.server.live_session)
        self.assertEqual(self.request('GET', f'/v1/live/{cid}/audio.wav')[0], 409)
        self.assertEqual(self.request('POST', f'/v1/live/{cid}/audition', '{}', {'Content-Type': 'application/json'})[0], 200)
        code, body = self.request('GET', f'/v1/live/{cid}/audio.wav')
        self.assertEqual(code, 200)
        self.assertEqual(body[:4], b'RIFF')

    def test_health_and_discard_remain_available_during_model_work(self):
        entered, release = threading.Event(), threading.Event()
        def blocked(features, cfg):
            entered.set()
            release.wait(2)
            return deterministic_plan('mirror', len(features['slices'])), 'fake'
        self.server.live_session = LiveSession(blocked)
        cid = capture(self.server.live_session, provider='model')
        self.server.live_session.finish(cid)
        self.assertTrue(entered.wait(1))
        try:
            self.assertEqual(self.request('GET', '/health')[0], 200)
            code, body = self.request('POST', f'/v1/live/{cid}/discard', '{}', {'Content-Type': 'application/json'})
            self.assertEqual(code, 200)
            self.assertEqual(json.loads(body)['state'], 'discarded')
        finally:
            release.set()
            wait(self.server.live_session)

    def test_origin_and_size_protections(self):
        self.assertEqual(self.request('GET', '/health', headers={'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.request('GET', '/health', headers={'Host': 'example.com'})[0], 403)
        cid = self.server.live_session.arm(config())['id']
        self.assertEqual(self.request('POST', f'/v1/live/{cid}/chunks/0', bytes(65538), {'Content-Type': 'application/octet-stream'})[0], 400)


class PlannerTests(unittest.TestCase):
    def test_loopback_only(self):
        for url in ('https://127.0.0.1/v1', 'http://example.com/v1', 'http://127.0.0.1:7332/other'):
            with self.assertRaises(ValueError):
                CorePlanner(url)

    def test_core_contract_and_stall_deadline(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                requests.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                if self.server.code != 200:
                    self.send_response(self.server.code)
                    self.end_headers()
                    return
                if self.server.stall:
                    time.sleep(0.3)
                    return
                data = json.dumps({'message': {'role': 'assistant', 'content': json.dumps(deterministic_plan('mirror', 1))}, 'model': 'fake'}).encode()
                if self.server.bad is not None:
                    data = self.server.bad
                self.send_response(200)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.stall = False
        server.code = 200
        server.bad = None
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            planner = CorePlanner(f'http://127.0.0.1:{server.server_address[1]}/v1', timeout=0.1)
            plan, model = planner({}, dict(mode='mirror', instruction=''))
            self.assertEqual(model, 'fake')
            self.assertEqual(requests[0][0], '/v1/chat')
            self.assertFalse(requests[0][1]['use_memory'])
            for code in (429, 502, 503, 504):
                server.code = code
                with self.assertRaises(ValueError):
                    planner({}, dict(mode='mirror', instruction=''))
            server.code = 200
            for bad in (b'invalid JSON', b'x' * 16385):
                server.bad = bad
                with self.assertRaises(ValueError):
                    planner({}, dict(mode='mirror', instruction=''))
            server.bad = None
            server.stall = True
            start = time.monotonic()
            with self.assertRaises((OSError, ValueError, http.client.HTTPException)):
                planner({}, dict(mode='mirror', instruction=''))
            self.assertLess(time.monotonic()-start, 0.25)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
