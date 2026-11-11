#!/usr/bin/env python3
"""Render ORIGINAL synth accompaniment for a live cover-led stage set.

These are deliberately simplified harmonic/rhythmic scaffolds, not
transcriptions, stems or any protected Radiohead audio. No downloads,
soundfonts, dependencies, model weights or internet required.
48 kHz, 16-bit stereo looping WAVs ship inside the stage app.
"""
from array import array
import math
import os
import random
import struct
import wave
from pathlib import Path

SR=48000
ROOT=Path(__file__).resolve().parent
OUT=Path(os.environ.get("SUZY_BACKING_DIR",ROOT/"backing"))
OUT.mkdir(parents=True,exist_ok=True)
TWOPI=2*math.pi
random.seed(29)

def make_buffer(seconds):
    n=round(seconds*SR)
    return [array("f",[0])*n,array("f",[0])*n]

def add_note(buf,start,duration,midi,velocity=.24,pan=0.0,tone="piano"):
    n=len(buf[0])
    begin=round(start*SR)
    total=min(round((duration+1.7)*SR),n)
    hz=440*2**((midi-69)/12)
    # Add the tail modulo loop so the seam is musical, not a click.
    left=.5-pan*.36
    right=.5+pan*.36
    for j in range(total):
        t=j/SR
        attack=1-math.exp(-t*210)
        release=math.exp(-3.8*max(0,t-duration))
        decay=math.exp((-2.1 if tone=="piano" else -1.1)*t)
        envelope=attack*release*decay
        if envelope < .00015: continue
        s=(math.sin(TWOPI*hz*t)
           +.33*math.sin(TWOPI*hz*2.008*t)*math.exp(-2.8*t)
           +.17*math.sin(TWOPI*hz*3.003*t)*math.exp(-4*t))
        sample=s*envelope*velocity
        pos=(begin+j)%n
        buf[0][pos]+=sample*left
        buf[1][pos]+=sample*right

def add_chord(buf,at,midi,vel=.25,hold=.5):
    for i,note in enumerate(midi):
        add_note(buf,at,hold,note,vel*(.86 if i else 1.0),pan=(i/(len(midi)-1)-.5)*.9)

def add_drum(buf,at,kind,level=.25):
    n=len(buf[0]); start=round(at*SR)
    length=int(SR*(.25 if kind=="kick" else .17))
    for j in range(length):
        t=j/SR
        env=math.exp(-t*(27 if kind=="hat" else 17))
        if kind=="kick":
            phase=TWOPI*(68*t-13*t*t)
            val=math.sin(phase)*env*level
        else:
            noise=random.uniform(-1,1)
            val=noise*env*level
        p=(start+j)%n
        buf[0][p]+=val*.48
        buf[1][p]+=val*.48

def write(name,buf):
    n=len(buf[0]); path=OUT/name
    with wave.open(str(path),"wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        block=4096
        for start in range(0,n,block):
            out=bytearray()
            for j in range(start,min(n,start+block)):
                # Conservative headroom: independent vocal and Magenta
                # need space. Soft limit, not destructive master loudness.
                l=math.tanh(buf[0][j]*.8)
                r=math.tanh(buf[1][j]*.8)
                out.extend(struct.pack("<hh",int(l*32700),int(r*32700)))
            f.writeframesraw(out)
    print(f"{name}: {n/SR:.3f}s {path.stat().st_size:,} bytes")

# PYRAMID: 3-3-4-3-3 eighth-note accents in two bars; a floating
# simplified close-voicing piano study supporting LIVE keyboard/voice.
bpm=105
eighth=30/bpm
groups=[3,3,4,3,3]
pyramid_chords=[
    [54,58,61,66], [55,59,62,66],
    [57,61,64,66], [55,59,62,66], [54,58,61,66]
]
repetitions=4
cycle=sum(groups)*eighth
buf=make_buffer(cycle*repetitions)
for cycle_num in range(repetitions):
    beat=0
    for ix,steps in enumerate(groups):
        at=(cycle_num*sum(groups)+beat)*eighth
        add_chord(buf,at,pyramid_chords[ix],vel=.31,hold=steps*eighth*.68)
        beat+=steps
write("pyramid.wav",buf)

# EVOLVE: original 8-bar sparse pulse, no Radiohead melodic material.
bpm=120
bar=60/bpm*4
buf=make_buffer(bar*8)
vocab=[[52,55,59,62],[57,61,64,66],[55,59,62,66],[54,57,61,64]]
for i in range(8):
    t=i*bar
    add_chord(buf,t+.05,vocab[i%4][1:],vel=.16,hold=1.2)
    add_note(buf,t+.03,.48,vocab[i%4][0]-12,.29,tone="warm")
    add_note(buf,t+bar*.75,.37,vocab[i%4][0]-12,.18,tone="warm")
    for k in range(4):
        add_drum(buf,t+k*60/bpm,"kick",.14 if k==0 else .055)
        if k in (1,3): add_drum(buf,t+k*60/bpm,"snare",.045)
        add_drum(buf,t+k*60/bpm+30/bpm,"hat",.017)
write("evolve.wav",buf)

# FISHES: a restrained repeating three-note arpeggio against four beats.
# Original instrument voicings/rhythm study, not the recorded guitar parts.
bpm=153
eighth=30/bpm
bar=eighth*8
chords=[[52,55,59,62],[54,57,61,64],[57,61,64,69],[55,59,62,66]]
buf=make_buffer(bar*8)
for i in range(8):
    start=i*bar
    chord=chords[i%4]
    for k in range(8):
        note=chord[(k+i)%3+1]
        add_note(buf,start+k*eighth,.18,note,.14,pan=(-.45 if k%2 else .45),tone="warm")
    add_note(buf,start,.36,chord[0]-12,.19,tone="warm")
write("fishes.wav",buf)
