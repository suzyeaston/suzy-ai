"""Bounded PCM processing, run off the host's audio callback thread."""
from array import array
import io
import math
import sys
import wave

MAX_SECONDS = 8
MAX_CHUNK = 65536


def decode(pcm: bytes) -> array:
    samples = array('h')
    samples.frombytes(pcm)
    if sys.byteorder != 'little':
        samples.byteswap()
    return samples


def describe(pcm: bytes, rate: int, channels: int, bpm: float) -> dict:
    samples = decode(pcm)
    frames = len(samples) // channels
    # Beat-sized source slices; at most 16. Timing comes from the host, not detection.
    slice_frames = max(round(rate * 60 / bpm), math.ceil(frames / 16))
    slices = []
    for start in range(0, frames, slice_frames):
        segment = samples[start * channels:min(frames, start + slice_frames) * channels]
        rms = math.sqrt(sum(float(v) * v for v in segment) / len(segment)) / 32768
        slices.append({'index': len(slices), 'start_frame': start,
                       'frames': len(segment) // channels, 'rms': round(rms, 5)})
    return {'sample_rate': rate, 'channels': channels, 'frames': frames,
            'duration_seconds': frames / rate, 'bpm_supplied': bpm,
            'peak': max(abs(v) for v in samples) / 32768, 'slices': slices}


def validate_plan(plan: object, count: int) -> dict:
    if not isinstance(plan, dict) or set(plan) != {'slices'}:
        raise ValueError('plan must contain only slices')
    entries = plan['slices']
    if not isinstance(entries, list) or len(entries) != count:
        raise ValueError('plan must preserve the number of source slices')
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'index', 'gain', 'reverse'}:
            raise ValueError('invalid slice fields')
        if type(entry['index']) is not int or not 0 <= entry['index'] < count:
            raise ValueError('invalid source slice')
        if type(entry['gain']) not in (int, float) or not math.isfinite(entry['gain']) or not 0 <= entry['gain'] <= 1:
            raise ValueError('invalid gain')
        if type(entry['reverse']) is not bool:
            raise ValueError('invalid reverse flag')
    return plan


def deterministic_plan(mode: str, count: int) -> dict:
    order = list(range(count))
    if mode == 'evolve' and count > 1:
        order = order[1:] + order[:1]
    return {'slices': [{'index': i, 'gain': 0.8, 'reverse': False} for i in order]}


def render(pcm: bytes, features: dict, plan: dict, mode: str) -> bytes:
    """Same-duration PCM WAV; source samples, not neural waveform synthesis.

    Short edge fades avoid cut clicks. AUGMENT overlays a quiet, one-beat-delayed
    response with the dry source; it does not infer a harmony or change pitch.
    """
    rate, channels = features['sample_rate'], features['channels']
    source = decode(pcm)
    output = array('h', [0]) * len(source)
    slots = features['slices']
    validate_plan(plan, len(slots))
    ceiling = int(32767 * 10 ** (-3 / 20))
    for slot, entry in zip(slots, plan['slices']):
        selected = slots[entry['index']]
        length = min(slot['frames'], selected['frames'])
        fade = max(1, min(round(rate * 0.005), length // 2))
        for frame in range(length):
            src_frame = selected['start_frame'] + (length - 1 - frame if entry['reverse'] else frame)
            envelope = min(1.0, frame / fade, (length - 1 - frame) / fade)
            for channel in range(channels):
                value = source[src_frame * channels + channel] * entry['gain'] * envelope
                output[(slot['start_frame'] + frame) * channels + channel] = round(max(-ceiling, min(ceiling, value)))
    if mode == 'augment':
        delay = round(rate * 60 / features['bpm_supplied']) * channels
        wet = output
        output = array('h', [0]) * len(source)
        fade = max(1, round(rate * 0.005))
        frames = len(source) // channels
        for i, value in enumerate(source):
            frame = i // channels
            envelope = min(1.0, frame / fade, (frames - 1 - frame) / fade)
            mixed = (value * 0.4 + (wet[i - delay] * 0.4 if i >= delay else 0)) * envelope
            output[i] = round(max(-ceiling, min(ceiling, mixed)))
    if sys.byteorder != 'little':
        output.byteswap()
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(output.tobytes())
    return buffer.getvalue()
