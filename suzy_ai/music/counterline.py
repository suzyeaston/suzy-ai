"""Offline symbolic counterline composition from estimated note events.

A constrained deterministic musical *generator*, not neural audio and not Qwen.
The live performance path is unchanged; no MIDI device / clock access here.
"""
from array import array
import io
import math
import sys
import wave

MIN_PITCH = 48
MAX_PITCH = 84
MAX_EVENTS = 12


def _snap(pitch, harmony):
    if harmony is None:
        return pitch
    if not isinstance(harmony, dict) or set(harmony) != {'root_pc', 'quality'}:
        raise ValueError('harmony must explicitly supply root_pc and quality')
    root, quality = harmony['root_pc'], harmony['quality']
    if type(root) is not int or not 0 <= root <= 11 or quality not in ('major', 'minor'):
        raise ValueError('invalid explicitly supplied chord')
    pcs = {(root+i)%12 for i in (0, 4 if quality == 'major' else 3, 7)}
    allowed = [p for p in range(MIN_PITCH, MAX_PITCH+1) if p%12 in pcs]
    return min(allowed, key=lambda p:(abs(p-pitch), p))


def compose_counterline(phrase: dict, *, register='above', density='full',
                        harmony=None, motion='contrary') -> dict:
    """Return new validated note events, staggered behind a captured melody.

    Contrapuntal motion is calculated from changes between source notes;
    it does not copy the recorded waveform or repeat a fixed four-note motif.
    Optional harmony is an explicit performer input, never inferred.
    """
    if register not in ('above', 'below') or density not in ('full', 'sparse'):
        raise ValueError('unknown register or density')
    if motion not in ('contrary', 'oblique'):
        raise ValueError('unknown movement strategy')
    _snap(60, harmony)
    if not isinstance(phrase, dict) or phrase.get('status') not in ('unvoiced', 'monophonic_candidate'):
        raise ValueError('invalid phrase status')
    bpm, seconds = phrase.get('bpm_supplied'), phrase.get('duration_seconds')
    if type(bpm) not in (int,float) or not math.isfinite(bpm) or not 40 <= bpm <= 240:
        raise ValueError('invalid supplied tempo')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0 < seconds <= 8:
        raise ValueError('invalid phrase duration')
    source = phrase.get('notes')
    if not isinstance(source,list) or len(source) > 32:
        raise ValueError('invalid phrase event list')
    total_beats = seconds*bpm/60
    previous_start = -1.0
    for n in source:
        if not isinstance(n,dict) or type(n.get('midi_note')) is not int or not 36 <= n['midi_note'] <= 84:
            raise ValueError('invalid source pitch')
        if any(type(n.get(k)) not in (int,float) or not math.isfinite(n[k]) for k in ('start_beats','duration_beats','confidence')):
            raise ValueError('invalid source time or confidence')
        if (not 0 <= n['confidence'] <= 1 or n['start_beats'] < previous_start
                or n['duration_beats'] <= 0 or n['start_beats']+n['duration_beats'] > total_beats+0.25):
            raise ValueError('invalid, unordered or out-of-range source events')
        previous_start = n['start_beats']
    if phrase['status'] == 'unvoiced' or not source:
        return {'status':'no_confident_melody', 'events':[], 'method':'constrained symbolic counterline',
                'bpm_supplied':bpm, 'duration_seconds':seconds}
    strong = [n for n in source if n['confidence'] >= 0.84]
    if len(strong) < 2:
        return {'status':'no_confident_melody', 'events':[], 'method':'constrained symbolic counterline',
                'bpm_supplied':bpm, 'duration_seconds':seconds}
    first = strong[0]['midi_note']
    answer_pitch = max(MIN_PITCH, min(MAX_PITCH, first + (7 if register=='above' else -7)))
    last_source = first
    ends = 0
    events=[]
    for index,n in enumerate(strong[:MAX_EVENTS]):
        interval=max(-7,min(7,n['midi_note']-last_source))
        if motion == 'contrary':
            answer_pitch = max(MIN_PITCH, min(MAX_PITCH, answer_pitch-interval))
        last_source = n['midi_note']
        if density == 'sparse' and index%2:
            continue
        start = max(ends+0.125, math.ceil(n['start_beats']*2)/2 + 0.5)
        if start >= total_beats-0.15:
            break
        duration=min(0.65,max(0.22,n['duration_beats']*.50),total_beats-start)
        if duration < 0.15:
            continue
        pitch=_snap(answer_pitch,harmony)
        events.append({'start_beats':round(start,3),'duration_beats':round(duration,3),
                       'midi_note':pitch,'velocity':68})
        ends = start+duration
    return {'status':'composed' if events else 'no_space',
            'events':events, 'method':'constrained symbolic counterline',
            'bpm_supplied':bpm, 'duration_seconds':seconds,
            'motion':motion, 'register':register, 'density':density,
            'harmony_source':'performer_supplied' if harmony is not None else 'none'}


def render_counterline(plan: dict, rate=48000) -> bytes:
    """Conservative audition-only dual-mono PCM16; not a stage transport."""
    if type(rate) is not int or rate not in (44100,48000):
        raise ValueError('unsupported audio rate')
    bpm,seconds=plan.get('bpm_supplied'),plan.get('duration_seconds')
    events=plan.get('events')
    if type(bpm) not in (int,float) or not math.isfinite(bpm) or not 40 <= bpm <= 240:
        raise ValueError('invalid tempo')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0 < seconds <= 8:
        raise ValueError('invalid duration')
    if not isinstance(events,list) or len(events) > MAX_EVENTS:
        raise ValueError('invalid events')
    frames=round(rate*seconds)
    out=array('h',[0])*(frames*2)
    for n in events:
        if not isinstance(n,dict) or set(n) != {'start_beats','duration_beats','midi_note','velocity'}:
            raise ValueError('invalid note fields')
        start,dur,pitch,vel=(n[k] for k in ('start_beats','duration_beats','midi_note','velocity'))
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (start,dur)) or start < 0 or dur <= 0:
            raise ValueError('invalid timing')
        if type(pitch) is not int or not MIN_PITCH <= pitch <= MAX_PITCH or type(vel) is not int or not 1 <= vel <= 127:
            raise ValueError('invalid MIDI event')
        offset=round(start*60/bpm*rate)
        count=min(round(dur*60/bpm*rate),frames-offset)
        if offset < 0 or offset >= frames or count <= 0:
            raise ValueError('note outside phrase')
        hz=440*2**((pitch-69)/12)
        fade=max(1,round(.015*rate))
        for i in range(count):
            env=min(1.0,i/fade,(count-1-i)/fade)
            theta=2*math.pi*hz*i/rate
            sample=round(32767*.04*vel/90*env*(math.sin(theta)+.15*math.sin(2*theta)))
            pos=(offset+i)*2
            for channel in (0,1):
                out[pos+channel]=max(-16000,min(16000,out[pos+channel]+sample))
    if sys.byteorder!='little':
        out.byteswap()
    return out.tobytes()


def audition_wav(plan: dict, rate=48000) -> bytes:
    """Return an in-memory stereo WAV for explicit offline listening."""
    pcm=render_counterline(plan,rate=rate)
    out=io.BytesIO()
    with wave.open(out,'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return out.getvalue()


if __name__=='__main__':
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description='Create a synthetic, original offline musical answer; no mic, MIDI or Qwen.')
    parser.add_argument('--demo-wav',required=True,help='output WAV path, created only when explicitly requested')
    args=parser.parse_args()
    demo={'status':'monophonic_candidate','bpm_supplied':120,'duration_seconds':4.0,
          'notes':[{'midi_note':n,'confidence':1.0,'start_beats':b,'duration_beats':.8}
                   for n,b in [(60,0),(64,2),(67,4),(64,6)]]}
    plan=compose_counterline(demo,harmony={'root_pc':0,'quality':'major'})
    Path(args.demo_wav).write_bytes(audition_wav(plan))
    print(f"Wrote offline answer to {args.demo_wav}: {plan['events']}")
