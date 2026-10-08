"""Explicit model setup and owned child-process launcher; never invoked by chat."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time

from .paths import ensure_home

MODEL_FILE = 'Qwen3-1.7B-Q4_K_M.gguf'
MODEL_REVISION = 'daeb8e2d528a760970442092f6bf1e55c3b659eb'
MODEL_SHA256 = 'd2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5'
MODEL_URL = (f'https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF/resolve/'
             f'{MODEL_REVISION}/{MODEL_FILE}')
MODEL_ALIAS = 'suzy-local'


def model_path() -> Path:
    return ensure_home() / 'models' / MODEL_FILE


def verified(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest() == MODEL_SHA256


def download() -> None:
    path = model_path()
    with (path.parent / '.download.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if verified(path):
            print('Model already downloaded and verified.')
            return
        if path.exists():
            raise RuntimeError('Existing model failed verification; move it aside before retrying.')
        if shutil.disk_usage(path.parent).free < 2_000_000_000:
            raise RuntimeError('At least 2 GB free disk space is required for the model download.')
        partial = path.with_suffix('.gguf.part')
        if partial.is_symlink():
            raise RuntimeError('Refusing a symlink at the partial download path.')
        print('Downloading Qwen3 1.7B Q4_K_M (about 1.28 GB). Interrupted downloads can resume.', flush=True)
        subprocess.run([
            'curl', '--fail', '--location', '--proto', '=https', '--proto-redir', '=https',
            '--retry', '3', '--connect-timeout', '30', '--speed-limit', '1024',
            '--speed-time', '120', '--continue-at', '-', '--output', str(partial), MODEL_URL,
        ], check=True)
        if not verified(partial):
            raise RuntimeError('Model checksum mismatch. Remove the .gguf.part file and run setup again.')
        partial.chmod(0o600)
        partial.replace(path)
        print('Model SHA-256 verified; saved in your private model directory.')


def request(port: int, path: str, payload: dict | None = None) -> dict:
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=125 if payload else 2)
    try:
        connection.request('POST' if payload is not None else 'GET', path,
                           json.dumps(payload) if payload is not None else None,
                           {'Content-Type': 'application/json'})
        response = connection.getresponse()
        raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise RuntimeError('Local API response exceeded the size limit.')
        data = json.loads(raw)
        if response.status != 200:
            raise RuntimeError(f'Local API returned HTTP {response.status}; check the configuration or shorten the message.')
        return data
    finally:
        connection.close()


def wait_ready(process: subprocess.Popen, port: int, timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'Local service exited with code {process.returncode}. Check the installed llama.cpp version and available memory.')
        try:
            health = request(port, '/health')
            if health.get('status') == 'ok' or health.get('ok') is True:
                return
        except (OSError, ValueError, RuntimeError, http.client.HTTPException):
            pass
        time.sleep(0.25)
    raise RuntimeError('Local service did not become ready within two minutes.')


def check_ports(ports: tuple[int, int]) -> None:
    if ports[0] == ports[1] or any(not 1024 <= port <= 65535 for port in ports):
        raise RuntimeError('Choose two different ports between 1024 and 65535.')
    for port in ports:
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                raise RuntimeError(f'Port {port} is already in use. Stop your existing service or choose another port; no process was killed.') from None


def model_command(binary: str, path: Path, port: int) -> list[str]:
    return [binary, '--model', str(path), '--alias', MODEL_ALIAS,
            '--host', '127.0.0.1', '--port', str(port), '--ctx-size', '4096',
            '--parallel', '1', '--batch-size', '256', '--ubatch-size', '128',
            '--threads', '4', '--n-gpu-layers', '99', '--jinja',
            '--chat-template-kwargs', '{"enable_thinking":false}',
            '--reasoning-budget', '0', '--offline', '--no-webui', '--log-disable']


def stop_owned(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def printable(value: str) -> str:
    # Model or stored text must not inject terminal escape/control sequences.
    return ''.join(c for c in value if c.isprintable() or c in '\n\t')


def conversation(port: int) -> None:
    print('\nSUZY//AI is ready. Type a message, /memory on, /memory off, /reset, or /quit.')
    print('Conversations stay in this process only. Memory retrieval starts OFF.')
    history: list[dict] = []
    use_memory = False
    while True:
        try:
            message = input('\nyou > ').strip()
        except EOFError:
            return
        if not message:
            continue
        if message == '/quit':
            return
        if message == '/reset':
            history.clear()
            print('Conversation cleared.')
            continue
        if message in ('/memory on', '/memory off'):
            use_memory = message.endswith('on')
            print(f'Memory retrieval {"ON" if use_memory else "OFF"}.')
            continue
        if len(message) > 2000:
            print('Please keep each message under 2,000 characters for this small model.')
            continue
        try:
            result = request(port, '/v1/chat', {'message': message, 'history': history,
                             'use_memory': use_memory, 'memory_limit': 3, 'max_tokens': 384})
        except (OSError, ValueError, RuntimeError, http.client.HTTPException) as exc:
            print(f'Chat unavailable: {exc}')
            continue
        answer = result['message']['content']
        print('\nSUZY > ' + printable(answer))
        if result['sources']:
            print('Retrieved sources: ' + ', '.join(s['id'] for s in result['sources']))
        history.extend([{'role': 'user', 'content': message}, {'role': 'assistant', 'content': answer}])
        while len(history) > 4 or sum(len(turn['content']) for turn in history) > 4000:
            del history[:2]


def run(api_port: int = 7331, model_port: int = 8081, no_chat: bool = False) -> None:
    check_ports((api_port, model_port))
    binary = shutil.which('llama-server')
    if not binary:
        raise RuntimeError('llama-server is missing. Run bash scripts/setup-mac.sh.')
    path = model_path()
    print('Verifying the local model…', flush=True)
    if not verified(path):
        raise RuntimeError('Verified model is missing. Run bash scripts/setup-mac.sh.')
    key = secrets.token_urlsafe(32)
    # Do not inherit runtime flags that could enable tools, downloads, logging,
    # alternate model paths, or remote endpoints.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('LLAMA_', 'HF_', 'SUZY_AI_'))}
    env['LLAMA_API_KEY'] = key
    core_env = env | {'SUZY_AI_HOME': str(ensure_home()), 'SUZY_AI_MODEL': MODEL_ALIAS,
                      'SUZY_AI_INFERENCE_URL': f'http://127.0.0.1:{model_port}/v1',
                      'SUZY_AI_INFERENCE_API_KEY': key, 'SUZY_AI_INFERENCE_TIMEOUT': '120'}
    children = []
    try:
        print('Loading the model; this can take a minute…', flush=True)
        model = subprocess.Popen(model_command(binary, path, model_port), env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        children.append(model)
        wait_ready(model, model_port)
        core = subprocess.Popen([sys.executable, '-m', 'suzy_ai.cli', 'serve',
                                 '--port', str(api_port)], env=core_env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        children.append(core)
        wait_ready(core, api_port, timeout=15)
        # Synthetic smoke test only; never read or write private memory here.
        request(api_port, '/v1/chat', {'message': 'Reply with a short hello.', 'max_tokens': 64})
        print(f'Local inference test passed. Core API: http://127.0.0.1:{api_port}', flush=True)
        if no_chat:
            print('Services running. Ctrl-C stops both.', flush=True)
            while all(child.poll() is None for child in children):
                time.sleep(0.5)
            raise RuntimeError('A local service stopped unexpectedly.')
        conversation(api_port)
    finally:
        for child in reversed(children):
            stop_owned(child)
        print('SUZY//AI services stopped.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['download', 'run'])
    parser.add_argument('--api-port', type=int, default=7331)
    parser.add_argument('--model-port', type=int, default=8081)
    parser.add_argument('--no-chat', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        if args.action == 'download':
            download()
        else:
            run(args.api_port, args.model_port, args.no_chat)
    except KeyboardInterrupt:
        print('\nStopped.')
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'SUZY//AI: {exc}', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
