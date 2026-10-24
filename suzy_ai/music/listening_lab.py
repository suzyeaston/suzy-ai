"""Offline, honest A/B of local Qwen with *actual* user WAVs (no stage routing).

Voice input becomes approximate note events; beat WAV becomes a 1/8th-note
energy envelope. Qwen receives NEITHER recording, just derived features and
an optional chord symbol supplied by the performer. Identical backing/voice
is mixed into two preview WAVs so the singer can hear the *arrangement*.
All work happens off the audio callback and on the local machine.
"""
from __future__ import annotations

from array import array
import argparse
import io
import json
import math
from pathlib import Path
import sys
import wave

from .phrase import extract_phrase
from .counterline import audition_wav
from .qwen_composer import LocalQwenComposer, CompositionError


def read_short_wav(path):
    """Bounded uncompressed mono/stereo 16-bit WAV, no resampling or network."""
    with wave.open(str(path), "rb") as f:
        rate, channels, width = f.getframerate(), f.getnchannels(), f.getsampwidth()
        count = f.getnframes()
        if f.getcomptype() != "NONE" or rate not in (44100, 48000) or channels not in (1, 2) or width != 2:
            raise ValueError("Use uncompressed PCM16 WAV at 44.1/48 kHz, mono or stereo")
        if not int(rate*1.5) <= count <= rate*8:
            raise ValueError("Supply a vocal/beat segment lasting 1.5-8 seconds")
        data=f.readframes(count)
        if len(data) != count*channels*2:
            raise ValueError("Truncated WAV audio")
    return {"rate":rate,"channels":channels,"frames":count,"pcm":data}


def _samples(wav):
    values=array("h")
    values.frombytes(wav["pcm"])
    if sys.byteorder != "little":
        values.byteswap()
    return values


def half_beat_energy(backing,bpm):
    """Relative RMS energy every half beat, not a tempo or drum-transcription AI."""
    if type(bpm) not in (int,float) or not math.isfinite(bpm) or not 40 <= bpm <= 240:
        raise ValueError("Supply actual Logic session BPM between 40 and 240")
    samples=_samples(backing)
    frames,rate,channels=backing["frames"],backing["rate"],backing["channels"]
    beats=frames*bpm/(rate*60)
    bins=math.ceil(beats*2)
    if bins > 32:
        raise ValueError("This bounded listener supports at most 16 beats")
    stride=60*rate/(bpm*2)
    results=[]
    for i in range(bins):
        start=round(i*stride)
        end=min(frames,round((i+1)*stride))
        if end <= start:
            results.append(0.0)
            continue
        # Sample at modest rate to stay cheap on an 8 GB machine.
        step=max(1,(end-start)//3000)
        sq=0
        n=0
        for frame in range(start,end,step):
            for c in range(channels):
                val=int(samples[frame*channels+c])
                sq+=val*val
                n+=1
        results.append(math.sqrt(sq/n) if n else 0.0)
    peak=max(results,default=0)
    return [round(v/peak,3) if peak > 0 else 0.0 for v in results]


def _stereo_sample(data, samples, frame, channel):
    if frame >= data["frames"]:
        return 0
    count=data["channels"]
    return int(samples[frame*count+(channel if count==2 else 0)])


def arrangement_preview(voice, backing, plan):
    """Preview with identical source bed for A and B and bounded headroom.

    This preview intentionally uses a plain sine synth; use Logic instruments
    for final musical judgments. Gains are fixed and are NOT mastered.
    """
    if voice["rate"] != backing["rate"] or voice["frames"] != backing["frames"]:
        raise ValueError("Voice and beat WAV must have matching rate and length; export one aligned Logic region")
    rate=voice["rate"]
    ai=audition_wav(plan,rate=rate)
    with wave.open(io.BytesIO(ai),"rb") as reader:
        ai_frames=reader.getnframes()
        if abs(ai_frames-voice["frames"]) > round(rate*.01) or reader.getnchannels()!=2:
            raise ValueError("AI reply does not match the supplied vocal region")
        ai_pcm=reader.readframes(ai_frames)
    ai_samples=array("h")
    ai_samples.frombytes(ai_pcm)
    if sys.byteorder!="little":ai_samples.byteswap()
    v,b=_samples(voice),_samples(backing)
    out=array("h")
    for i in range(voice["frames"]):
        for c in (0,1):
            x=(0.26*_stereo_sample(backing,b,i,c)+
               0.30*_stereo_sample(voice,v,i,c)+
               (1.35*ai_samples[2*i+c] if i<ai_frames else 0))
            out.append(int(max(-28000,min(28000,round(x)))))
    if sys.byteorder!="little":out.byteswap()
    target=io.BytesIO()
    with wave.open(target,"wb") as writer:
        writer.setnchannels(2)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(out.tobytes())
    return target.getvalue()


def compare(voice_path,beat_path,*,bpm,chord=None,query,out_dir,composer=None):
    """Explicitly run A vs B over the same actual recording; no fake result."""
    voice,beat=read_short_wav(voice_path),read_short_wav(beat_path)
    if voice["rate"] != beat["rate"] or voice["frames"] != beat["frames"]:
        raise ValueError("Export aligned voice and beat regions of equal length and sample rate")
    if any(not isinstance(x,str) for x in (query,out_dir)):
        raise ValueError("Invalid experiment fields")
    phrase=extract_phrase(voice["pcm"],rate=voice["rate"],
                          channels=voice["channels"],bpm=bpm)
    grid=half_beat_energy(beat,bpm)
    observed={"chord":chord,"half_beat_energy":grid}
    runner=composer or LocalQwenComposer()
    options=(("A_no_research",False),("B_with_research",True))
    results={}
    for name,grounded in options:
        plan=runner(phrase,instruction=query,
                    use_deep_research=grounded,accompaniment=observed)
        results[name]={"model":plan["model"],
                       "note_events":plan["events"],
                       "reference_used":plan["reference_used"],
                       "references_offered":plan["references_offered"]}
        results[name]["_plan"]=plan
    target=Path(out_dir).expanduser()
    target.mkdir(parents=True,exist_ok=True)
    for name in results:
        preview=arrangement_preview(voice,beat,results[name].pop("_plan"))
        (target/(name+".wav")).write_bytes(preview)
    a=results[options[0][0]]["note_events"]
    b=results[options[1][0]]["note_events"]
    report={
        "type":"LOCAL_QWEN_REAL_INPUT_AB",
        "not_proof_of_learning":True,
        "voice_source":"local_user_supplied_wav",
        "beat_source":"local_user_supplied_wav",
        "beat_analysis":"half-beat RMS only; no drum-source/key recognition",
        "bpm_supplied":bpm,"chord_supplied":chord,
        "lead_notes_detected":len(phrase.get("notes",[])),
        "source_duration_seconds":voice["frames"]/voice["rate"],
        "half_beat_energy":grid,
        "A_no_research":results[options[0][0]],
        "B_with_research":results[options[1][0]],
        "identical_note_events":a==b,
        "warning":"Plain sine preview. Compare in Logic with real instruments; two similar melodies do not show cultural learning.",
    }
    (target/"comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    return report


def main():
    p=argparse.ArgumentParser(description="Real-vocal, real-beat local Qwen A/B; offline and not a live routing tool")
    p.add_argument("--voice-wav",required=True,help="vocal-only aligned WAV")
    p.add_argument("--beat-wav",required=True,help="beat-only aligned WAV")
    p.add_argument("--bpm",required=True,type=float,help="real Logic project tempo")
    p.add_argument("--chord",default=None,help="optional chord symbol supplied by you, e.g. Am9")
    p.add_argument("--query",default="Original 90s R&B hip hop call and response with space for vocals")
    p.add_argument("--out-dir",required=True,help="explicit local directory to write A/B preview WAVs and report")
    args=p.parse_args()
    result=compare(args.voice_wav,args.beat_wav,bpm=args.bpm,chord=args.chord,query=args.query,out_dir=args.out_dir)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    print("Auditions are in",Path(args.out_dir).expanduser())


if __name__=="__main__":
    main()
