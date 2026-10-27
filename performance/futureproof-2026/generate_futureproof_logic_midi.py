#!/usr/bin/env python3
"""SUZY//AI Futureproof 2026: original deterministic Logic MIDI backing.

Standard MIDI File format 1, stdlib-only. No Radiohead melody, samples,
or copyrighted recordings: harmony/rhythm scaffolds for Suzy's live medley.
The clock, phrasing, panic safety and audio recording stay with Logic Pro.
"""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path

PPQ = 480
BAR = PPQ * 4
EIGHTH = PPQ // 2
S1 = 126  # bars of floating opening, 105 BPM = 4:48
S2 = 60   # bars of original transformation, 120 BPM = 2:00
S3 = 313  # bars of closing arpeggios, 153 BPM = 8:11.0
SCENES = (("PYRAMID", 105, S1), ("TRANSFORMATION", 120, S2), ("FISHES", 153, S3))

P = [(54, 58, 61, 66), (55, 59, 62, 66), (57, 61, 64, 66),
     (55, 59, 62, 66), (54, 58, 61, 66)]
T = [(52, 55, 59, 62), (57, 61, 64, 66), (55, 59, 62, 66),
     (54, 57, 61, 64)]
F = [(52, 55, 59, 62), (54, 57, 61, 64), (57, 61, 64, 69),
     (55, 59, 62, 66)]

def vlq(n: int) -> bytes:
    assert n >= 0
    b = [n & 0x7f]
    n >>= 7
    while n:
        b.insert(0, (n & 0x7f) | 0x80)
        n >>= 7
    return bytes(b)

def meta(code: int, value: bytes) -> bytes:
    return bytes((0xff, code)) + vlq(len(value)) + value

def midi_track(name: str, channel: int | None = None, program: int | None = None):
    e = [(0, 0, meta(0x03, name.encode('utf-8')))]
    if channel is not None and program is not None:
        e.append((0, 1, bytes((0xc0 + channel, program))))
    return e

def note(events, channel, at, length, pitch, velocity):
    if length <= 0: return
    assert 0 <= pitch < 128 and 1 <= velocity <= 127
    events.append((int(at), 3, bytes((0x90 + channel, pitch, velocity))))
    events.append((int(at + length), 0, bytes((0x80 + channel, pitch, 0))))

def chord(events, channel, at, duration, pitches, velocity):
    for i, n in enumerate(pitches):
        note(events, channel, at + i * 9, duration - i * 9, n, max(10, velocity - i * 2))

def marker(events, bar_zero_based, label):
    events.append((bar_zero_based * BAR, 2, meta(0x06, label.encode('utf-8'))))

def finish(events):
    events = sorted(events, key=lambda x: (x[0], x[1]))
    out = bytearray()
    previous = 0
    for tick, _, content in events:
        if tick < previous: raise ValueError('time reversal')
        out.extend(vlq(tick - previous))
        out.extend(content)
        previous = tick
    out.extend(b'\x00\xff\x2f\x00')
    return b'MTrk' + struct.pack('>I', len(out)) + out

def write_midi(path, tracks):
    content = b''.join(finish(t) for t in tracks)
    header = b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), PPQ)
    path.write_bytes(header + content)

def make_full():
    conductor = midi_track('CONDUCTOR / 4-4 / SCENE MARKERS')
    conductor.append((0, 1, meta(0x58, b'\x04\x02\x18\x08')))
    conductor.append((0, 2, meta(0x51, round(60_000_000 / 105).to_bytes(3, 'big'))))
    conductor.append((S1 * BAR, 1, meta(0x51, round(60_000_000 / 120).to_bytes(3, 'big'))))
    conductor.append(((S1 + S2) * BAR, 1, meta(0x51, round(60_000_000 / 153).to_bytes(3, 'big'))))
    for b, label in [
        (0, 'PYRAMID / first chord and voice'),
        (16, 'PYRAMID / introduce upper voices'),
        (64, 'PYRAMID / bring AI in softly if stable'),
        (112, 'PYRAMID / prepare dissolve'),
        (126, 'TRANSFORMATION / hold E / capture fragment'),
        (150, 'TRANSFORMATION / begin 3-against-4 pulse'),
        (174, 'TRANSFORMATION / handoff / arm Fishes'),
        (186, 'WEIRD FISHES / first arpeggio'),
        (218, 'FISHES / voice returns'),
        (258, 'FISHES / add counterline'),
        (350, 'FISHES / expand / improvise'),
        (458, 'FISHES / reduce layers / prepare ending'),
        (491, 'ENDING / hold final harmony / AI mute'),
        (499, 'MANUAL END / all note offs')
    ]: marker(conductor, b, label)
    piano = midi_track('01 PYRAMID / FLOAT PIANO', 0, 0)
    pad = midi_track('02 TRANSITION / AIR PAD', 1, 89)
    arp1 = midi_track('03 FISHES / ARPEGGIO LEFT', 2, 10)
    arp2 = midi_track('04 FISHES / COUNTER ARP RIGHT', 3, 11)
    bass = midi_track('05 LOW NOTES / ENTER GRADUALLY', 4, 38)
    drums = midi_track('06 OPTIONAL PULSE / DRUM KIT', 9, None)
    ai = midi_track('07 OPTIONAL MRT2 MIDI HARMONY CUES', 5, 88)
    # Pyramid: five harmony attacks over two 4/4 bars, asymmetric 3+3+4+3+3 eighths.
    group = (3, 3, 4, 3, 3)
    for cycle in range(S1 // 2):
        start = cycle * 2 * BAR
        phase = min(cycle * 2, S1 - 1)
        dynamics = (38 if phase < 16 else 43 if phase < 64 else 48 if phase < 112 else 34)
        eighth_pos = 0
        for idx, n_eighth in enumerate(group):
            hit = start + eighth_pos * EIGHTH
            # original voicings derived from a chord map; no Radiohead melody.
            notes = P[idx]
            if phase < 16: notes = notes[1:]  # leave the lowest register for Suzy.
            chord(piano, 0, hit, int(n_eighth * EIGHTH * 0.75), notes, dynamics)
            eighth_pos += n_eighth
        if 32 <= phase < 112 and cycle % 4 == 0:
            note(pad, 1, start + 2 * EIGHTH, BAR * 2 - EIGHTH, P[cycle % 5][-1] + 12, 27)
        if phase >= 80 and phase < 112 and cycle % 2 == 0:
            note(bass, 4, start, BAR - 30, P[cycle % 5][0] - 12, 30)
        if 64 <= phase < 112 and cycle % 4 == 0:
            chord(ai, 5, start, 2 * BAR - 12, P[cycle % 5], 34)

    # Bridge / original material: sustained harmony, fragments of 3/8 across 4/4.
    t0 = S1 * BAR
    for i in range(S2):
        start = t0 + i * BAR
        c = T[(i // 2) % 4]
        if i % 2 == 0:
            chord(pad, 1, start, 2 * BAR - 60, c[1:], 33 if i < 16 else 39)
            note(bass, 4, start, BAR + PPQ, c[0] - 12, 33)
        if i >= 16:
            for j in range(0, 8, 3):
                note(piano, 0, start + j * EIGHTH, EIGHTH, c[(i + j) % 3 + 1] + 12, 30 + min(16, i // 4))
        if i >= 40:
            note(drums, 9, start, PPQ // 8, 36, 43)
            if i % 2 == 0: note(drums, 9, start + 2 * PPQ, PPQ // 10, 38, 35)
        if i % 8 == 0:
            chord(ai, 5, start, 2 * BAR - 10, c, 38)

    # Fishes: interlocking 3-eighth-note figures against a four-beat bar.
    # Original counterpoint, not a transcription of the guitar recording.
    f0 = (S1 + S2) * BAR
    end = f0 + S3 * BAR
    for i in range(S3):
        start = f0 + i * BAR
        c = F[(i // 2) % 4]
        if i < 305:
            note(bass, 4, start, 2 * PPQ, c[0] - 12, 41 if i < 48 else 49)
        # Long harmonic restraint means Suzy has room for singing.
        if i % 4 == 0 and i < 288:
            chord(pad, 1, start, 2 * BAR - 40, c[1:], 24)
        if i < 305:
            for k in range(8):
                global_eighth = i * 8 + k
                if global_eighth % 3 == 0:
                    note(arp1, 2, start + k * EIGHTH, round(EIGHTH * .82), c[1 + (global_eighth // 3) % 3] + 12, 46 if i < 32 else 53)
                if i >= 72 and (global_eighth - 1) % 3 == 0:
                    note(arp2, 3, start + k * EIGHTH, round(EIGHTH * .70), c[1 + ((global_eighth + 2) // 3) % 3] + 24, 25 if i < 156 else 31)
        if i >= 32 and i < 282:
            note(drums, 9, start, PPQ // 8, 36, 40 if i < 100 else 56)
            if i >= 88:
                note(drums, 9, start + 2 * PPQ, PPQ // 8, 38, 42)
            if i >= 160 and i % 2 == 0:
                for eighth in (2, 6):
                    note(drums, 9, start + eighth * EIGHTH, PPQ // 10, 42, 24)
        if i % 8 == 0 and i < 292:
            chord(ai, 5, start, 2 * BAR - 20, c, 32)
    # Last 8 bars: all moving parts stop; settle on held Em harmony.
    chord(pad, 1, f0 + 305 * BAR, 7 * BAR, (52, 55, 59, 62, 67), 42)
    chord(piano, 0, f0 + 310 * BAR, 2 * BAR, (52, 55, 59, 62), 48)
    return [conductor, piano, pad, arp1, arp2, bass, drums, ai]

def make_excerpt(all_tracks, start_bar: int, n_bars: int, bpm: int, name: str):
    # Clips are independently openable files, with tempo from tick zero.
    start, stop = start_bar * BAR, (start_bar + n_bars) * BAR
    tracks = []
    for i, src in enumerate(all_tracks):
        extracted = []
        for tick, priority, data in src:
            if not start <= tick < stop: continue
            if data.startswith(b'\xff\x51') or data.startswith(b'\xff\x58'): continue
            if data.startswith(b'\xff\x06'): continue
            extracted.append((tick - start, priority, data))
        if i == 0:
            extracted.append((0, 1, meta(0x58, b'\x04\x02\x18\x08')))
            extracted.append((0, 1, meta(0x51, round(60_000_000 / bpm).to_bytes(3,'big'))))
            extracted.append((0, 2, meta(0x06, name.encode('utf-8'))))
        tracks.append(extracted)
    return tracks

def make(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    tracks = make_full()
    write_midi(out/'SUZY_FUTUREPROOF_15min_FULL_SET.mid', tracks)
    write_midi(out/'SUZY_PYRAMID_FIRST_16_BARS.mid', make_excerpt(tracks,0,16,105,'REHEARSAL / PYRAMID FIRST 16 BARS'))
    write_midi(out/'SUZY_TRANSFORMATION_32_BARS.mid', make_excerpt(tracks,S1,32,120,'REHEARSAL / TRANSITION FIRST 32 BARS'))
    write_midi(out/'SUZY_FISHES_FIRST_32_BARS.mid', make_excerpt(tracks,S1+S2,32,153,'REHEARSAL / FISHES FIRST 32 BARS'))
    duration = S1*4*60/105+S2*4*60/120+S3*4*60/153
    data={'format':1,'ticks_per_quarter':PPQ,'total_bars':sum(x[2] for x in SCENES),'duration_seconds':round(duration,3),
      'acts':[{'name':name,'bpm':bpm,'bars':bars,'duration_seconds':round(bars*4*60/bpm,2)} for name,bpm,bars in SCENES],
      'files':['SUZY_FUTUREPROOF_15min_FULL_SET.mid','SUZY_PYRAMID_FIRST_16_BARS.mid','SUZY_TRANSFORMATION_32_BARS.mid','SUZY_FISHES_FIRST_32_BARS.mid']}
    (out/'show_map.json').write_text(json.dumps(data,indent=2)+'\n')
    return data

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent)
    a=p.parse_args()
    print(json.dumps(make(a.out),indent=2))
