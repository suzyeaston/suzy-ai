"""Small, bounded DSP descriptors. No transcription, chord detection or neural audio."""
import math
from collections import Counter


def musical_features(samples, rate, channels):
    # Collapse to mono, box-filter before decimating to ~8 kHz.
    # On Scarlett, a vocal often occupies only one input (L), while R is
    # silent. Averaging two inputs would halve the already-quiet signal and
    # suppress pitch detection. Pick the dominant mono input *only* when the
    # other channel's measured energy is at least 20x lower.
    selected = None
    if channels == 2:
        stride = max(1, (len(samples) // 2) // 4096)
        energy_l = sum(float(samples[2 * i]) ** 2
                       for i in range(0, len(samples) // 2, stride))
        energy_r = sum(float(samples[2 * i + 1]) ** 2
                       for i in range(0, len(samples) // 2, stride))
        if energy_l > 400 * energy_r:
            selected = 0
        elif energy_r > 400 * energy_l:
            selected = 1
    hop = rate // 8000
    if selected is None:
        mono = [sum(samples[i:i + hop * channels]) / (hop * channels * 32768)
                for i in range(0, len(samples) - hop * channels + 1, hop * channels)]
    else:
        mono = [sum(samples[i + selected:i + hop * channels:channels]) / (hop * 32768)
                for i in range(0, len(samples) - hop * channels + 1, hop * channels)]
    sr = rate / hop
    window = round(sr * .02)
    energy = [math.sqrt(sum(x*x for x in mono[i:i+window]) / len(mono[i:i+window]))
              for i in range(0, len(mono), window)]
    onsets = []
    previous = 0.0
    for i, value in enumerate(energy):
        if value > .01 and value > max(.005, previous) * 1.8 and (not onsets or i*.02-onsets[-1] >= .08):
            onsets.append(round(i*.02, 3))
        previous = value
    notes = []
    # At most eight short windows. Only a monophonic pitch hint, never a chord/key claim.
    width = min(1024, len(mono))
    for k in range(min(8, max(1, len(mono)//width))):
        offset = round(k * max(0, len(mono)-width) / 7)
        x = mono[offset:offset+width]
        mean = sum(x) / len(x)
        x = [v-mean for v in x]
        if sum(v*v for v in x)/len(x) < .000025:
            continue
        correlations = []
        for lag in range(max(2, round(sr/1000)), min(round(sr/75), len(x)//2)):
            a, b = x[:-lag], x[lag:]
            denominator = math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
            correlations.append((lag, sum(v*w for v,w in zip(a,b))/denominator if denominator else 0))
        peaks = [(lag, score) for i,(lag,score) in enumerate(correlations[1:-1],1)
                 if score >= .85 and score >= correlations[i-1][1] and score > correlations[i+1][1]]
        if peaks:
            best = max(score for _,score in peaks)
            lag, confidence = next((lag,score) for lag,score in peaks if score >= best*.98)
            midi = round(69 + 12*math.log2((sr/lag)/440))
            notes.append({'time_seconds': round(offset/sr, 3), 'midi_note': midi,
                          'confidence': round(confidence, 3)})
    counts = Counter(note['midi_note'] % 12 for note in notes)
    return {'onset_seconds': onsets[:64], 'pitch_hints': notes,
            'pitch_class_counts': dict(sorted(counts.items())),
            'method': 'energy-rise and monophonic autocorrelation; polyphonic/noisy input may be wrong',
            'key_detected': None, 'chords_detected': None}
