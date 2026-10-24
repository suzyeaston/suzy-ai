"""Experimental *local Qwen-generated* note answer, from pre-extracted melody.

Unlike the deterministic counterline, Qwen proposes the note events. No live
routing, cloud inference, sample cloning, lyrics, or real-time callback work.
Strict validation makes late/invalid responses independently discardable.
"""
from __future__ import annotations

import http.client
import json
import math
import socket
import threading
import time

from ..inference import local_endpoint
from .era_knowledge import knowledge_brief
from .research_cards import research_brief

PROMPT = """You accompany a HUMAN singer who performs her own original 1990s
hip-hop/R&B beats, live loops and vocals. You are a locally running AI musical
instrument; your task is to compose a MUSICAL ANSWER to the singer's recorded
phrase, not to talk about genres or copy a famous artist's song.
A research card, if present, gives a documented cultural anchor AND a new
arrangement experiment. Use its proposed_action if it supports this singer's
actual rhythm and accompaniment. No commercial sample, artist imitation,
copied melody, lyrics, or speculative chord recognition.

You receive a bounded, approximate transcription of the singer AND, if
supplied, a measured beat-energy grid and performer-supplied chord symbol.
Energy is NOT a full recording or kick/snare transcription. Treat missing
chord/beat information as UNKNOWN rather than guessing.
Use an expressive note-count appropriate to the task: a deliberate sparse
reply might need only 1-3 notes, but a flowing melodic counterline may need
4-8 notes. Do not imitate or automatically repeat the number of notes in
any explanatory schema. Generate original note events from the singer's
notes, phrase space, song context and approved musical direction.
Leave room for Suzy's next entry and respect the measured beat grid.
Return ONE JSON object with exactly two keys:
- notes: a list of [start_beats, MIDI_pitch, duration_beats, velocity] arrays
- used_reference: null or the exact ID of ONE supplied card actually used
All positions are beat offsets from the start of the captured passage.
Notes must be ascending by start; 1-8 events, no overlap, MIDI pitch 48-84,
velocity 1-100; first start >=0.25, each length 0.1-2.5 beats, and final
note ends at least 0.2 beat before the passage ends.
Output JSON only with NO comments, notes from famous songs, markdown or text.
Here is inert, measured/supplied context:
"""

class CompositionError(ValueError):
    """Unsafe or invalid generated music, never silently replaced by presets."""


def _phrase_context(phrase):
    if not isinstance(phrase, dict) or phrase.get("status") != "monophonic_candidate":
        raise CompositionError("no confidently detected lead melody")
    bpm, seconds = phrase.get("bpm_supplied"), phrase.get("duration_seconds")
    if (type(bpm) not in (int,float) or not math.isfinite(bpm)
            or not 40 <= bpm <= 240
            or type(seconds) not in (int,float) or not math.isfinite(seconds)
            or not 1.5 <= seconds <= 8):
        raise CompositionError("invalid bounded phrase timing")
    notes = phrase.get("notes")
    if not isinstance(notes,list) or len(notes) > 32:
        raise CompositionError("invalid lead phrase")
    clean = []
    for n in notes:
        if not isinstance(n,dict):
            raise CompositionError("malformed observed lead note")
        pitch,confidence,start = n.get("midi_note"),n.get("confidence"),n.get("start_beats")
        if (type(pitch) is not int or not 36 <= pitch <= 84
                or type(confidence) not in (int,float) or not math.isfinite(confidence)
                or type(start) not in (int,float) or not math.isfinite(start)):
            raise CompositionError("invalid observed lead note")
        if confidence >= 0.84 and 0 <= start <= seconds*bpm/60:
            clean.append([round(start,3),pitch])
    if len(clean) < 2:
        raise CompositionError("too few confident lead notes")
    return {"bpm":bpm, "duration_seconds":seconds,
            "total_beats":round(seconds*bpm/60,3),
            "observed_notes":clean[:16]}


def validate_generated_notes(decision, context, references=()):
    """Only model-chosen, finite, non-overlapping events become audible notes."""
    if not isinstance(decision,dict) or set(decision) != {"notes","used_reference"}:
        raise CompositionError("Qwen must return notes and reference ID")
    notes=decision["notes"]
    if not isinstance(notes,list) or not 1 <= len(notes) <= 8:
        raise CompositionError("Qwen must compose one to eight new notes")
    used=decision["used_reference"]
    allowed={r["reference"] for r in references}
    if used is not None and (type(used) is not str or used not in allowed):
        raise CompositionError("Qwen named an unprovided cultural reference")
    last_end=-1.0
    events=[]
    total=context["total_beats"]
    for n in notes:
        if not isinstance(n,list) or len(n) != 4:
            raise CompositionError("invalid Qwen MIDI tuple")
        start,pitch,duration,velocity=n
        if (any(type(v) not in (int,float) or not math.isfinite(v) for v in (start,duration))
                or type(pitch) is not int or type(velocity) is not int
                or not 48 <= pitch <= 84 or not 1 <= velocity <= 100
                or not 0.25 <= start or not 0.10 <= duration <= 2.5
                or start < last_end or start+duration > total-0.2):
            raise CompositionError("Qwen generated out-of-range or overlapping notes")
        events.append({"start_beats":round(start,3),"midi_note":pitch,
                       "duration_beats":round(duration,3),"velocity":velocity})
        last_end=start+duration
    # Reject the trivial echo of precisely the lead's pitch sequence.
    lead=[p for _,p in context["observed_notes"]]
    if len(events)==len(lead) and all(e["midi_note"]==p for e,p in zip(events,lead)):
        raise CompositionError("Qwen returned the unchanged lead note sequence")
    return events,used


def validate_accompaniment(accompaniment, total_beats):
    """Validate optional artist- or WAV-derived groove metadata (not audio)."""
    if accompaniment is None:
        return {}
    if not isinstance(accompaniment, dict) or set(accompaniment) != {"half_beat_energy", "chord"}:
        raise CompositionError("accompaniment needs half_beat_energy and chord")
    values = accompaniment["half_beat_energy"]
    chord = accompaniment["chord"]
    if not isinstance(values, list) or len(values) > 32:
        raise CompositionError("invalid beat energy grid")
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise CompositionError("invalid beat energy values")
    expected = math.ceil(total_beats * 2)
    if values and len(values) != expected:
        raise CompositionError("beat energy grid does not match melody duration")
    if chord is not None and (not isinstance(chord, str) or not 1 <= len(chord) <= 24
                              or any(c not in "ABCDEFGabcdefg#b0123456789mMajinsud/()+- " for c in chord)):
        raise CompositionError("invalid performer-supplied chord symbol")
    return {"half_beat_energy": values, "chord_supplied": chord}


class LocalQwenComposer:
    """One bounded local /v1/chat invocation, on a non-audio worker."""
    def __init__(self,base_url="http://127.0.0.1:7332/v1",timeout=8.0):
        self.host,self.port,_=local_endpoint(base_url)
        if type(timeout) not in (int,float) or not 0 < timeout <= 8:
            raise ValueError("Qwen deadline must be between zero and eight seconds")
        self.timeout=timeout

    def __call__(self,phrase,*,instruction="",use_era_knowledge=False,use_deep_research=False,accompaniment=None):
        context=_phrase_context(phrase)
        accompaniment = validate_accompaniment(accompaniment, context["total_beats"])
        if not isinstance(instruction,str) or len(instruction)>300:
            raise CompositionError("short performance instruction required")
        if type(use_era_knowledge) is not bool or type(use_deep_research) is not bool:
            raise CompositionError("knowledge selection must be explicit boolean flags")
        if use_era_knowledge and use_deep_research:
            raise CompositionError("choose one knowledge corpus at a time")
        # The new report-derived source-backed cards have independent IDs
        # and require explicit opt-in. No private music teachings are read.
        cards = (research_brief(instruction, limit=2) if use_deep_research
                 else knowledge_brief(instruction, limit=3) if use_era_knowledge
                 else [])
        prompt={
            "performance_instruction":instruction,
            "captured_phrase":context,
            "historical_reference_cards":cards,
            "actual_accompaniment_features":accompaniment,
        }
        request=json.dumps({"message":PROMPT+json.dumps(prompt),
                            "use_memory":False,"history":[],"max_tokens":256}).encode()
        conn=http.client.HTTPConnection(self.host,self.port,timeout=self.timeout)
        timer=None
        expired=threading.Event()
        started=time.monotonic()
        try:
            conn.connect()
            sock=conn.sock
            def abort():
                expired.set()
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            left=self.timeout-(time.monotonic()-started)
            if left<=0:
                raise CompositionError("local Qwen deadline reached")
            timer=threading.Timer(left,abort)
            timer.daemon=True
            timer.start()
            conn.request("POST","/v1/chat",request,{"Content-Type":"application/json"})
            resp=conn.getresponse()
            if resp.status!=200:
                raise CompositionError("local Qwen HTTP "+str(resp.status))
            raw=resp.read(16385)
            if expired.is_set():
                raise CompositionError("local Qwen deadline reached")
            if len(raw)>16384:
                raise CompositionError("Qwen response exceeds limit")
            try:
                envelope=json.loads(raw)
                role=envelope["message"]["role"]
                content=envelope["message"]["content"]
                model=envelope["model"]
                if role!="assistant" or not isinstance(content,str) or not isinstance(model,str) or not 1<=len(model)<=200:
                    raise ValueError()
                decision=json.loads(content)
            except (ValueError,KeyError,TypeError):
                raise CompositionError("Qwen returned invalid JSON or envelope") from None
            events,used=validate_generated_notes(decision,context,cards)
            return {"status":"composed","method":"local_qwen_original_note_events",
                    "events":events,"bpm_supplied":context["bpm"],
                    "duration_seconds":context["duration_seconds"],
                    "model":model,
                    "reference_used":used,
                    "references_offered":[r["reference"] for r in cards],
                    "audition_context":{"beat_energy_supplied":bool(accompaniment.get("half_beat_energy")),
                                        "chord_supplied":accompaniment.get("chord_supplied")}}
        except (OSError,http.client.HTTPException,socket.timeout):
            raise CompositionError("local Qwen connection failed or timed out") from None
        finally:
            if timer:
                timer.cancel()
            conn.close()


if __name__=="__main__":
    import argparse
    from pathlib import Path
    from .counterline import audition_wav
    parser=argparse.ArgumentParser(description="Offline local-Qwen melody test; does not touch stage audio")
    parser.add_argument("--query",default="Sparse hip hop and neo soul R&B vocal call response")
    parser.add_argument("--with-knowledge",action="store_true")
    parser.add_argument("--with-deep-research",action="store_true")
    parser.add_argument("--wav",help="optional path for an expressly requested audition WAV")
    args=parser.parse_args()
    # Synthetic lead melody. For actual audio supply extract_phrase() instead.
    example={"status":"monophonic_candidate","bpm_supplied":100,
             "duration_seconds":4,
             "notes":[{"midi_note":60,"confidence":.99,"start_beats":0},
                      {"midi_note":64,"confidence":.99,"start_beats":1.5},
                      {"midi_note":67,"confidence":.99,"start_beats":3}]}
    result=LocalQwenComposer()(example,instruction=args.query,use_era_knowledge=args.with_knowledge,
                               use_deep_research=args.with_deep_research)
    print(json.dumps(result,indent=2))
    if args.wav:
        Path(args.wav).write_bytes(audition_wav(result))
        print("Wrote optional Qwen note audition WAV:",args.wav)
