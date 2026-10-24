"""Optional post-capture, bounded monophonic phrase observations.

No model, I/O, chords/key inference, live callbacks or third-party packages.
False and missing pitches are possible, especially on harmony/processed vocals.
"""
from array import array
import math
import statistics
import sys

MAX_SECONDS = 8
MAX_NOTES = 32


def _mono(pcm: bytes, rate: int, channels: int):
    samples = array('h')
    samples.frombytes(pcm)
    if sys.byteorder != 'little':
        samples.byteswap()
    frames = len(samples) // channels
    # Don't halve a one-sided Scarlett microphone by averaging it with silence.
    selected = None
    if channels == 2:
        stride = max(1, frames // 4096)
        left = sum(int(samples[2*i])**2 for i in range(0, frames, stride))
        right = sum(int(samples[2*i+1])**2 for i in range(0, frames, stride))
        if left > 400*right:
            selected = 0
        elif right > 400*left:
            selected = 1
    hop = max(1, round(rate / 8000))
    mono = []
    for i in range(0, frames - hop + 1, hop):
        if selected is None:
            mono.append(sum(samples[i*channels:(i+hop)*channels]) / (hop*channels*32768))
        else:
            mono.append(sum(samples[i*channels+selected:(i+hop)*channels:channels]) / (hop*32768))
    return mono, rate/hop


def _pitch(window, sr):
    """Conservative normalized autocorrelation over a 45ms vocal window."""
    mean = sum(window)/len(window)
    x = [value-mean for value in window]
    rms = math.sqrt(sum(v*v for v in x)/len(x))
    if rms < 0.0025:
        return None, 0.0, rms
    low = max(2, round(sr/900))
    high = min(round(sr/90), len(x)//2)
    scores = []
    # Off callback; sub-sampling limits CPU on eight-second clips.
    for lag in range(low, high+1):
        a = b = dot = 0.0
        for j in range(0, len(x)-lag, 4):
            p, q = x[j], x[j+lag]
            a += p*p
            b += q*q
            dot += p*q
        scores.append((lag, dot/math.sqrt(a*b) if a*b > 0 else 0.0))
    best = max((score for _, score in scores), default=0)
    if best < 0.84:
        return None, 0.0, rms
    # Select the shortest convincing local period; higher multiples can also
    # correlate strongly, especially for pure tones.
    candidates = [(lag, score) for k,(lag,score) in enumerate(scores)
                  if score >= max(0.84, best-0.025)
                  and score >= scores[max(0,k-1)][1]
                  and score >= scores[min(len(scores)-1,k+1)][1]]
    if not candidates:
        return None, 0.0, rms
    lag, confidence = min(candidates, key=lambda item: item[0])
    midi = round(69+12*math.log2((sr/lag)/440))
    if not 36 <= midi <= 84:
        return None, 0.0, rms
    return midi, round(confidence, 3), rms


def extract_phrase(pcm: bytes, rate: int, channels: int, bpm: float) -> dict:
    """Return estimated note events, with rests, contour and uncertainty.

    Input is interleaved little-endian PCM16 up to eight seconds. Timing is
    relative to capture, with BPM supplied by the performer/host. This is
    NOT robust transcription, harmony detection, or a real-time render API.
    """
    if type(rate) is not int or rate not in (44100, 48000):
        raise ValueError('rate must be 44100 or 48000')
    if type(channels) is not int or channels not in (1, 2):
        raise ValueError('channels must be one or two')
    if type(bpm) not in (int, float) or not math.isfinite(bpm) or not 40 <= bpm <= 240:
        raise ValueError('BPM must be finite and between 40 and 240')
    if not isinstance(pcm, bytes) or not pcm or len(pcm) % (2*channels):
        raise ValueError('PCM16 must contain whole frames')
    frames = len(pcm)//(2*channels)
    if frames > MAX_SECONDS*rate:
        raise ValueError('phrase cannot exceed eight seconds')
    duration = frames/rate
    mono, sr = _mono(pcm, rate, channels)
    size = max(192, round(sr*0.045))
    step = max(80, round(sr*0.02))
    if len(mono) < size:
        return _result([], [], duration, bpm)
    observations = []
    for pos in range(0, len(mono)-size+1, step):
        note, confidence, rms = _pitch(mono[pos:pos+size], sr)
        observations.append((pos/sr, note, confidence, rms))
    if not observations:
        return _result([], [], duration, bpm)
    # Discard pitches close to a loud phrase's noise floor; fixed absolute
    # threshold in _pitch protects genuinely silent signals.
    active_rms = [r for _,p,_,r in observations if p is not None]
    floor = max(0.0025, max(active_rms, default=0)*0.15)
    timeline = [(time, p if rms >= floor else None, confidence)
                for time,p,confidence,rms in observations]
    # Fill one-frame pitch gaps only when neighboring pitches match.
    corrected = list(timeline)
    for i in range(1, len(timeline)-1):
        prev, cur, nxt = timeline[i-1:i+2]
        if cur[1] is None and prev[1] is not None and prev[1] == nxt[1]:
            corrected[i] = (cur[0], prev[1], min(prev[2], nxt[2]))
    runs = []
    begin = 0
    for i in range(1, len(corrected)+1):
        if i == len(corrected) or corrected[i][1] != corrected[begin][1]:
            pitch = corrected[begin][1]
            # Windows give boundaries a ~20ms uncertainty; no sample-accurate
            # note timing is claimed.
            start = corrected[begin][0]
            end = min(duration, corrected[i-1][0]+size/sr)
            if end-start >= 0.08:
                runs.append((pitch, start, end, [x[2] for x in corrected[begin:i]]))
            begin = i
    notes = []
    rests = []
    for pitch, start, end, confidences in runs:
        event = {'start_seconds': round(start, 3), 'duration_seconds': round(end-start, 3),
                 'start_beats': round(start*bpm/60, 3),
                 'duration_beats': round((end-start)*bpm/60, 3)}
        if pitch is None:
            rests.append(event)
        else:
            notes.append({**event, 'midi_note': pitch,
                          'confidence': round(statistics.median(confidences), 3)})
    return _result(notes[:MAX_NOTES], rests[:MAX_NOTES], duration, bpm)


def _result(notes, rests, duration, bpm):
    intervals = [right['midi_note']-left['midi_note'] for left,right in zip(notes, notes[1:])]
    return {'status': 'monophonic_candidate' if notes else 'unvoiced',
            'method': 'windowed normalized autocorrelation, approximate monophonic events',
            'duration_seconds': round(duration, 3), 'bpm_supplied': bpm,
            'notes': notes, 'rests': rests, 'intervals': intervals,
            'contour': ['up' if n>0 else 'down' if n<0 else 'same' for n in intervals],
            'key_detected': None, 'chords_detected': None}
