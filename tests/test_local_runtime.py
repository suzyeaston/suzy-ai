import contextlib
import hashlib
import io
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from suzy_ai import local_runtime as local
from suzy_ai.inference import LocalInference
from test_v03 import FakeModel, running


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'SUZY_AI_HOME': self.tmp.name})
        env.start()
        self.addCleanup(env.stop)

    def test_download_checksum_atomic_install_and_reuse(self):
        synthetic = b'synthetic model fixture'
        digest = hashlib.sha256(synthetic).hexdigest()
        def fake_download(args, **kwargs):
            self.assertIn('--continue-at', args)
            self.assertIn(local.MODEL_REVISION, args[-1])
            Path(args[args.index('--output') + 1]).write_bytes(synthetic)
        with patch.object(local, 'MODEL_SHA256', digest), patch.object(local.subprocess, 'run', side_effect=fake_download) as run:
            local.download()
            self.assertTrue(local.verified(local.model_path()))
            local.download()
            self.assertEqual(run.call_count, 1)
        self.assertEqual(local.model_path().stat().st_mode & 0o777, 0o600)

    def test_checksum_failure_never_installs_partial(self):
        def corrupt(args, **kwargs):
            Path(args[args.index('--output') + 1]).write_bytes(b'corrupt')
        with patch.object(local.subprocess, 'run', side_effect=corrupt):
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                local.download()
        self.assertFalse(local.model_path().exists())
        self.assertTrue(local.model_path().with_suffix('.gguf.part').exists())

    def test_existing_corrupt_model_is_preserved(self):
        path = local.model_path()
        path.write_bytes(b'do not overwrite')
        with self.assertRaisesRegex(RuntimeError, 'move it aside'):
            local.download()
        self.assertEqual(path.read_bytes(), b'do not overwrite')

    def test_occupied_port_never_kills_existing_service(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
            with self.assertRaisesRegex(RuntimeError, 'already in use'):
                local.check_ports((port, 7332 if port != 7332 else 7333))
        with self.assertRaises(RuntimeError):
            local.check_ports((7331, 7331))

    def test_launch_settings_and_cleanup_on_failure(self):
        model, core = Mock(), Mock()
        model.poll.return_value = core.poll.return_value = None
        commands = []
        def spawn(args, **kwargs):
            commands.append((args, kwargs))
            return model if len(commands) == 1 else core
        with patch.object(local, 'check_ports'), patch.object(local.shutil, 'which', return_value='/fake/llama-server'), patch.object(local, 'verified', return_value=True), patch.object(local, 'wait_ready'), patch.object(local.subprocess, 'Popen', side_effect=spawn), patch.object(local, 'request', side_effect=RuntimeError('synthetic failure')), patch.dict(os.environ, {'LLAMA_ARG_TOOLS': 'all', 'LLAMA_ARG_HOST': '0.0.0.0'}):
            with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
                local.run()
        argv, kwargs = commands[0]
        self.assertIn('--offline', argv)
        self.assertIn('--no-webui', argv)
        self.assertIn('--log-disable', argv)
        self.assertEqual(argv[argv.index('--host') + 1], '127.0.0.1')
        self.assertEqual(argv[argv.index('--ctx-size') + 1], '4096')
        self.assertNotIn('LLAMA_ARG_TOOLS', kwargs['env'])
        self.assertNotIn('LLAMA_ARG_HOST', kwargs['env'])
        key = kwargs['env']['LLAMA_API_KEY']
        self.assertTrue(key)
        self.assertNotIn(key, argv)
        self.assertEqual(commands[1][1]['env']['SUZY_AI_INFERENCE_API_KEY'], key)
        model.terminate.assert_called_once()
        core.terminate.assert_called_once()

    def test_cleanup_escalates_only_owned_child(self):
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired('fake', 5), 0]
        local.stop_owned(child)
        child.terminate.assert_called_once()
        child.kill.assert_called_once()

    def test_conversation_memory_opt_in_reset_and_controls(self):
        calls = []
        def reply(port, path, body):
            calls.append(dict(body, history=list(body['history'])))
            return {'message': {'content': 'hello'}, 'sources': []}
        with patch('builtins.input', side_effect=['first', '/memory on', 'second', '/reset', '/memory off', 'third', '/quit']), patch.object(local, 'request', side_effect=reply), contextlib.redirect_stdout(io.StringIO()):
            local.conversation(7331)
        self.assertTrue(calls[0]['use_memory'])
        self.assertTrue(calls[1]['use_memory'])
        self.assertEqual(len(calls[1]['history']), 2)
        self.assertEqual(calls[2]['history'], [])
        self.assertFalse(calls[2]['use_memory'])
        self.assertNotIn('\x1b', local.printable('\x1b[31mhello'))

    def test_inference_auth_header_and_secret_redaction(self):
        class AuthModel(FakeModel):
            auth = None
            def do_POST(self):
                type(self).auth = self.headers.get('Authorization')
                super().do_POST()
        with running(AuthModel) as server:
            adapter = LocalInference(f'http://127.0.0.1:{server.server_port}/v1', 'test', api_key='synthetic-secret')
            adapter.complete([], 10)
            self.assertEqual(AuthModel.auth, 'Bearer synthetic-secret')
            self.assertNotIn('synthetic-secret', repr(adapter))
        with self.assertRaises(ValueError):
            LocalInference('http://127.0.0.1:8081/v1', 'test', api_key='bad\nheader')
