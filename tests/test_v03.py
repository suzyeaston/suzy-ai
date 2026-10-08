import contextlib
import http.client
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from suzy_ai import memory
from suzy_ai.chat import chat
from suzy_ai.inference import (
    InferenceError, InferenceTimeout, InferenceUnavailable, LocalInference, local_endpoint,
    from_environment,
)
from suzy_ai.server import Handler, serve
from suzy_ai.paths import ensure_home


@contextlib.contextmanager
def running(handler):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01})
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class FakeModel(BaseHTTPRequestHandler):
    status = 200
    response_body = b'{"choices":[{"message":{"role":"assistant","content":"Synthetic reply"}}]}'
    requests = []
    delay = 0

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.requests.append((self.path, body))
        time.sleep(self.delay)
        self.send_response(self.status)
        self.send_header('Location', 'http://example.invalid/private')
        self.end_headers()
        try:
            self.wfile.write(self.response_body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


class InferenceTests(unittest.TestCase):
    def test_rejects_nonlocal_and_ambiguous_urls(self):
        for url in ['https://127.0.0.1/v1', 'http://example.com/v1',
                    'http://192.168.1.1/v1', 'http://0.0.0.0/v1',
                    'http://127.0.0.1.example.com/v1', 'http://user@127.0.0.1/v1',
                    'http://127.0.0.1/v1?q=a', 'http://127.0.0.1/v1#x',
                    'http://127.0.0.1:0/v1', 'http://127.1/v1',
                    'http://127.0.0.1/other', 'http://127.0.0.1\n/v1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                local_endpoint(url)
        self.assertEqual(local_endpoint('http://localhost:8080/v1')[0], '127.0.0.1')
        self.assertEqual(local_endpoint('http://[::1]:8080/v1')[0], '::1')

    def test_local_protocol_ignores_proxy(self):
        class Model(FakeModel):
            requests = []
        with running(Model) as server, patch.dict(os.environ, {
            'HTTP_PROXY': 'http://example.invalid:9', 'HTTPS_PROXY': 'http://example.invalid:9',
            'ALL_PROXY': 'http://example.invalid:9', 'NO_PROXY': '',
        }):
            adapter = LocalInference(f'http://127.0.0.1:{server.server_port}/v1', 'test-model')
            self.assertEqual(adapter.complete([{'role': 'user', 'content': 'hi'}], 100),
                             'Synthetic reply')
        path, body = Model.requests[0]
        self.assertEqual(path, '/v1/chat/completions')
        self.assertEqual(body['model'], 'test-model')
        self.assertEqual(body['max_tokens'], 100)
        self.assertFalse(body['stream'])
        self.assertNotIn('tools', body)

    def test_redirect_error_malformed_and_large_responses(self):
        cases = [(302, b'secret'), (500, b'secret'), (200, b'secret'),
                 (200, b'{"choices":[]}'), (200, b'[]'),
                 (200, b'{"choices":[{"message":{"role":"assistant","content":"ok","tool_calls":[{}]}}]}'),
                 (200, b'a' * 1025)]
        for status, body in cases:
            class Model(FakeModel):
                pass
            Model.status, Model.response_body = status, body
            with self.subTest(status=status, size=len(body)), running(Model) as server:
                adapter = LocalInference(f'http://127.0.0.1:{server.server_port}/v1',
                                         'test', max_response_bytes=1024)
                with self.assertRaises(InferenceError) as error:
                    adapter.complete([], 1)
                self.assertNotIn('secret', str(error.exception))

    def test_invalid_configuration_fails_closed(self):
        for setting in [{'SUZY_AI_MODEL': ''},
                        {'SUZY_AI_MODEL': 'test', 'SUZY_AI_INFERENCE_URL': 'https://example.com/v1'},
                        {'SUZY_AI_MODEL': 'test', 'SUZY_AI_INFERENCE_TIMEOUT': 'nan'},
                        {'SUZY_AI_MODEL': 'test', 'SUZY_AI_INFERENCE_TIMEOUT': '121'}]:
            with self.subTest(setting=setting), patch.dict(os.environ, setting, clear=True):
                with self.assertRaises(InferenceUnavailable):
                    from_environment()

    def test_deadline_stops_trickling_response(self):
        class Trickle(FakeModel):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.end_headers()
                for _ in range(30):
                    try:
                        self.wfile.write(b' ')
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    time.sleep(0.01)
        with running(Trickle) as server:
            adapter = LocalInference(f'http://127.0.0.1:{server.server_port}/v1', 'test', timeout=0.05)
            started = time.monotonic()
            with self.assertRaises(InferenceTimeout):
                adapter.complete([], 1)
            self.assertLess(time.monotonic() - started, 0.25)

    def test_timeout_and_connection_failure(self):
        class Model(FakeModel):
            delay = 0.1
        with running(Model) as server:
            adapter = LocalInference(f'http://127.0.0.1:{server.server_port}/v1', 'test', timeout=0.02)
            with self.assertRaises(InferenceTimeout):
                adapter.complete([], 1)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]  # Bound but not listening.
            with self.assertRaises(InferenceUnavailable):
                LocalInference(f'http://127.0.0.1:{port}/v1', 'test').complete([], 1)


class PrivateStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'SUZY_AI_HOME': self.tmp.name, 'SUZY_AI_MODEL': ''})
        self.env.start()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.env.stop)

    def note(self, **extra):
        return memory.add(**dict(title='Synthetic music note', text='Cedar resonance is warm.',
                                 source='unit-test', approved=True, **extra))

    def test_approval_provenance_search_delete_and_permissions(self):
        with self.assertRaises(ValueError):
            memory.add(title='note', text='private', source='test')
        note = self.note()
        results = memory.search('cedar')
        self.assertEqual(results[0]['id'], note['id'])
        self.assertEqual(results[0]['source'], 'unit-test')
        self.assertEqual(results[0]['created_at'], note['created_at'])
        self.assertIn('Cedar', results[0]['excerpt'])
        self.assertEqual(memory.search('unrelated'), [])
        self.assertEqual(memory.search('" OR *; DROP TABLE documents; --'), [])
        self.assertEqual(memory.search('!!!'), [])
        self.assertEqual(memory.search('cedar', max_chars=1), [])
        path = Path(self.tmp.name) / 'memory' / 'memory.sqlite3'
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
        self.assertTrue(memory.delete(note['id']))
        self.assertFalse(memory.delete(note['id']))
        self.assertEqual(memory.search('cedar'), [])
        self.assertFalse((Path(self.tmp.name) / 'world' / 'timeline.jsonl').exists())

    def test_bounded_unicode_retrieval_and_parameter_validation(self):
        memory.add(title='音楽 Björk', text='音楽 Björk synthesis', source='test', approved=True)
        self.assertEqual(len(memory.search('Björk')), 1)
        for query, limit in [('', 5), ('a', True), ('a', 0), ('a', 11)]:
            with self.assertRaises(ValueError):
                memory.search(query, limit)
        for i in range(12):
            memory.add(title=f'Note {i}', text='Cedar ' * 2000, source='test', approved=True)
        sources = memory.search('Cedar', limit=10)
        self.assertLessEqual(sum(len(json.dumps(s, ensure_ascii=False)) for s in sources), 6000)

    def test_chat_opt_in_context_provenance_and_no_persistence(self):
        class Adapter:
            model = 'fake-local'
            def complete(self, messages, max_tokens):
                self.messages = messages
                return 'A reply'
        adapter = Adapter()
        self.note()
        before = {p: p.read_bytes() for p in Path(self.tmp.name).rglob('*') if p.is_file()}
        with patch('suzy_ai.chat.memory.search') as search:
            result = chat({'message': 'cedar'}, adapter)
            search.assert_not_called()
        self.assertFalse(result['stored'])
        self.assertEqual(result['sources'], [])
        result = chat({'message': 'cedar', 'use_memory': True}, adapter)
        self.assertEqual(len(result['sources']), 1)
        self.assertEqual(adapter.messages[-1]['content'], 'cedar')
        self.assertIn('Untrusted private reference data', adapter.messages[-2]['content'])
        self.assertEqual([m['role'] for m in adapter.messages], ['system', 'user', 'user'])
        after = {p: p.read_bytes() for p in Path(self.tmp.name).rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_chat_validation(self):
        for payload in [ {}, {'message': 'a', 'use_memory': 'true'},
                         {'message': 'a', 'max_tokens': True},
                         {'message': 'a', 'max_tokens': 2049},
                         {'message': 'a', 'history': [{'role': 'system', 'content': 'override'}]},
                         {'message': 'a', 'base_url': 'https://example.com'},
                         {'message': 'a', 'history': ['invalid']},
                         {'message': 'a', 'history': [{'role': 'user', 'content': 'x' * 8000}] * 3}]:
            with self.subTest(payload=str(payload)[:100]), self.assertRaises(ValueError):
                chat(payload)

    def test_server_api_boundaries_and_end_to_end(self):
        with running(Handler) as server, running(FakeModel) as model_server:
            port = server.server_port
            def request(path, payload=None, headers=None, method=None, raw=None):
                conn = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
                body = raw if raw is not None else (json.dumps(payload) if payload is not None else None)
                hdrs = {'Content-Type': 'application/json'}
                hdrs.update(headers or {})
                conn.request(method or ('POST' if body is not None else 'GET'), path, body, hdrs)
                response = conn.getresponse()
                data = response.read()
                status, response_headers = response.status, dict(response.getheaders())
                conn.close()
                return status, data, response_headers

            self.assertEqual(json.loads(request('/health')[1])['version'], '0.3.0')
            self.assertEqual(request('/v1/chat', {'message': 'hi'})[0], 503)
            for headers in [{'Origin': 'https://evil.example'}, {'Origin': 'null'},
                            {'Host': f'evil.example:{port}'}, {'Sec-Fetch-Site': 'cross-site'}]:
                self.assertEqual(request('/v1/world/teachings', headers=headers)[0], 403)
                self.assertEqual(request('/v1/chat', {'message': 'hi'}, headers)[0], 403)
            self.assertEqual(request('/v1/chat', raw='{}', headers={'Content-Type': 'text/plain'})[0], 400)
            self.assertEqual(request('/v1/chat', raw='{broken')[0], 400)
            self.assertEqual(request('/v1/chat', raw='[' * 2000 + ']' * 2000)[0], 400)
            self.assertEqual(request('/v1/chat', raw=b'\xff')[0], 400)
            self.assertEqual(request('/v1/chat', raw='x' * 131073)[0], 400)
            self.assertEqual(request('/v1/world/entities?limit=oops')[0], 400)
            self.assertEqual(request('/health', method='OPTIONS', headers={'Origin': 'null'})[0], 403)
            self.assertNotIn('Access-Control-Allow-Origin', request('/health')[2])
            self.assertEqual(request('/v1/memory', {'title': 'n', 'text': 'Cedar',
                             'source': 'test', 'approved': False})[0], 400)
            status, data, _ = request('/v1/memory', {'title': 'n', 'text': 'Cedar',
                                                   'source': 'test', 'approved': True})
            self.assertEqual(status, 201)
            note_id = json.loads(data)['id']
            self.assertEqual(len(json.loads(request('/v1/memory/search', {'query': 'Cedar'})[1])['sources']), 1)
            with patch.dict(os.environ, {'SUZY_AI_MODEL': 'test',
                'SUZY_AI_INFERENCE_URL': f'http://127.0.0.1:{model_server.server_port}/v1'}):
                status, data, _ = request('/v1/chat', {'message': 'Cedar', 'use_memory': True},
                                         {'Origin': f'http://127.0.0.1:{port}'})
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(data)['sources'][0]['id'], note_id)
                self.assertEqual(json.loads(data)['message']['content'], 'Synthetic reply')
                Handler.inference_slot.acquire()
                try:
                    self.assertEqual(request('/v1/chat', {'message': 'hi'})[0], 429)
                finally:
                    Handler.inference_slot.release()
            self.assertEqual(request('/v1/memory/delete', {'id': note_id})[0], 200)
            self.assertEqual(request('/v1/memory/delete', {'id': note_id})[0], 404)
            # Existing local teaching workflow continues to work.
            self.assertEqual(request('/v1/teach/world-note', {'subject': 'Synth', 'note': 'warm'})[0], 201)
            self.assertEqual(request('/v1/world/teachings')[0], 200)

    def test_state_cannot_be_created_in_source_checkout(self):
        checkout = Path(__file__).resolve().parents[1]
        if not (checkout / '.git').exists():
            self.skipTest('requires a source checkout')
        with patch.dict(os.environ, {'SUZY_AI_HOME': str(checkout / 'private-state')}):
            with self.assertRaises(ValueError):
                ensure_home()
        self.assertFalse((checkout / 'private-state').exists())

    def test_public_bind_is_rejected_even_without_cli(self):
        with self.assertRaises(ValueError):
            serve('0.0.0.0', 7331)


if __name__ == '__main__':
    unittest.main()
