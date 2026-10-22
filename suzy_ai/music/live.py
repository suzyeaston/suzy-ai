"""One bounded capture and one asynchronous response worker per process.

Transport adapters must call this from a non-real-time thread. This Python object
is not a lock-free native audio buffer and must never run in a Logic render block.
"""
import copy
import hashlib
import math
import threading
import time
import uuid

from .planner import CorePlanner, ModelPlanningError
from .audio import MAX_CHUNK, MAX_SECONDS, describe, deterministic_plan, render, validate_plan


class Conflict(ValueError):
    pass


class LiveSession:
    def __init__(self, planner=None, core_url="http://127.0.0.1:7332/v1"):
        self._lock = threading.Lock()
        self._planner = planner or CorePlanner(core_url)
        self._worker = None
        self._id = None
        self._state = 'idle'
        self._pcm = bytearray()
        self._wav = None
        self._manifest = None
        self._error = None
        self._config = None
        self._sequence = 0
        self._history = []

    def status(self):
        with self._lock:
            return self._status()

    def _status(self):
        return {'protocol_version': 2, 'id': self._id, 'state': self._state,
                'busy': self._worker is not None and self._worker.is_alive(),
                'captured_bytes': len(self._pcm), 'next_sequence': self._sequence,
                'error': self._error, 'response': copy.deepcopy(self._manifest),
                'performance_context': copy.deepcopy(self._history)}

    def arm(self, payload):
        if not isinstance(payload, dict) or set(payload) - {'sample_rate', 'channels', 'bpm', 'mode', 'provider', 'instruction', 'section', 'key'}:
            raise ValueError('unsupported capture fields')
        rate, channels = payload.get('sample_rate'), payload.get('channels')
        bpm, mode = payload.get('bpm'), payload.get('mode')
        provider = payload.get('provider', 'deterministic')
        instruction = payload.get('instruction', '')
        section, key = payload.get('section', ''), payload.get('key', '')
        if not isinstance(section, str) or len(section) > 64 or not isinstance(key, str) or len(key) > 24:
            raise ValueError('section/key exceed text limits')
        if type(rate) is not int or rate not in (44100, 48000) or type(channels) is not int or channels not in (1, 2):
            raise ValueError('use 44100/48000 Hz and one or two channels')
        if type(bpm) not in (int, float) or not math.isfinite(bpm) or not 40 <= bpm <= 240:
            raise ValueError('host BPM must be between 40 and 240')
        if mode not in ('mirror', 'augment', 'evolve') or provider not in ('deterministic', 'model'):
            raise ValueError('invalid mode or provider')
        if not isinstance(instruction, str) or len(instruction) > 500:
            raise ValueError('instruction must be at most 500 characters')
        with self._lock:
            if self._state not in ('idle', 'accepted', 'failed', 'discarded') or (self._worker and self._worker.is_alive()):
                raise Conflict('finish or discard the current phrase; wait for any worker to exit')
            self._id = uuid.uuid4().hex
            self._config = dict(sample_rate=rate, channels=channels, bpm=bpm, mode=mode,
                                provider=provider, instruction=instruction, section=section, key=key,
                                performance_context=copy.deepcopy(self._history))
            self._pcm = bytearray()
            self._sequence = 0
            self._wav = self._manifest = self._error = None
            self._state = 'capturing'
            return self._status()

    def _check(self, capture_id, states):
        if capture_id != self._id or self._state not in states:
            raise Conflict('stale capture id or invalid state')

    def append(self, capture_id, sequence, pcm):
        with self._lock:
            self._check(capture_id, ('capturing',))
            if type(sequence) is not int or sequence != self._sequence:
                raise Conflict('out-of-order chunk; use next_sequence')
            if not isinstance(pcm, bytes) or not pcm or len(pcm) > MAX_CHUNK or len(pcm) % (2 * self._config['channels']):
                raise ValueError('send aligned PCM16LE chunks of 1–65536 bytes')
            maximum = MAX_SECONDS * self._config['sample_rate'] * self._config['channels'] * 2
            if len(self._pcm) + len(pcm) > maximum:
                raise ValueError('eight-second capture limit reached; finish or discard')
            self._pcm.extend(pcm)
            self._sequence += 1
            return self._status()

    def finish(self, capture_id):
        with self._lock:
            self._check(capture_id, ('capturing',))
            config = dict(self._config)
            if len(self._pcm) < config['sample_rate'] * config['channels'] * 2 / 4:
                raise ValueError('capture at least 0.25 seconds')
            pcm = bytes(self._pcm)
            self._pcm.clear()
            self._state = 'processing'
            self._worker = threading.Thread(target=self._respond, args=(capture_id, pcm, config), daemon=True)
            self._worker.start()
            return self._status()

    def _respond(self, capture_id, pcm, config):
        started = time.monotonic()
        phase = "audio analysis"
        try:
            features = describe(pcm, config['sample_rate'], config['channels'], config['bpm'])
            if features['peak'] < 0.001:
                raise ValueError('capture is silent or too quiet')
            phase = "model planning"
            if config['provider'] == 'model':
                plan, model = self._planner(features, config)
            else:
                plan, model = deterministic_plan(config['mode'], len(features['slices'])), None
            phase = "plan validation"
            validate_plan(plan, len(features['slices']))
            phase = "audio rendering"
            wav = render(pcm, features, plan, config['mode'])
            manifest = {'schema_version': '0.1', 'source_sha256': hashlib.sha256(pcm).hexdigest(),
                        'features': features, 'mode': config['mode'], 'provider': config['provider'],
                        'model': model, 'plan': plan, 'rendering': 'deterministic-source-audio-dsp',
                        'neural_audio_generation': False, 'section': config['section'], 'key_supplied': config['key'],
                        'context_used': config['performance_context'], 'elapsed_seconds': time.monotonic() - started}
            with self._lock:
                if capture_id == self._id and self._state == 'processing':
                    self._wav, self._manifest, self._state = wav, manifest, 'ready'
        except Exception as exc:
            # Only stable, hard-coded failure categories; never expose private
            # prompt material, audio features, model output or backend bodies.
            if phase == "model planning" and isinstance(exc, ModelPlanningError):
                reason = str(exc)  # ModelPlanningError is created only from fixed categories.
            elif phase == "plan validation" and isinstance(exc, ValueError):
                permitted = {
                    'plan must contain only slices',
                    'plan must preserve the number of source slices',
                    'invalid slice fields',
                    'invalid source slice',
                    'invalid gain',
                    'invalid reverse flag',
                }
                reason = str(exc) if str(exc) in permitted else "invalid slice arrangement"
            elif phase == "audio analysis" and str(exc) == 'capture is silent or too quiet':
                reason = "microphone signal too quiet"
            else:
                reason = "unexpected error (details withheld)"
            with self._lock:
                if capture_id == self._id and self._state == 'processing':
                    self._error = f'response failed during {phase}: {reason}'
                    self._state = 'failed'

    def action(self, capture_id, action):
        allowed = {'audition': ('ready', 'auditioning'), 'stop-audition': ('auditioning',),
                   'accept': ('ready', 'auditioning', 'accepted'),
                   'discard': ('capturing', 'processing', 'ready', 'auditioning', 'accepted', 'failed')}
        targets = {'audition': 'auditioning', 'stop-audition': 'ready',
                   'accept': 'accepted', 'discard': 'discarded'}
        if action not in allowed:
            raise ValueError('unknown response action')
        with self._lock:
            self._check(capture_id, allowed[action])
            if action == 'accept' and self._state != 'accepted':
                entries = self._manifest['plan']['slices']
                self._history.append({'mode': self._manifest['mode'], 'section': self._config['section'],
                    'key_supplied': self._config['key'], 'bpm': self._config['bpm'],
                    'slice_order': [e['index'] for e in entries],
                    'reversed_slices': sum(e['reverse'] for e in entries),
                    'pitch_class_counts': self._manifest['features']['musical']['pitch_class_counts']})
                self._history = self._history[-4:]
            self._state = targets[action]
            if action == 'discard':
                self._pcm.clear()
                self._wav = self._manifest = self._error = None
            return self._status()

    def audio(self, capture_id):
        with self._lock:
            self._check(capture_id, ('auditioning', 'accepted'))
            return self._wav

    def reset_context(self):
        with self._lock:
            self._history.clear()
            return self._status()
