"""Simple synthesized call-and-response for the experimental live audio probe.

The local text model chooses a *gesture*, not waveform samples. This lightweight
off-callback synthesizer uses only the captured phrase's uncertain monophonic
pitch hints to make an audible note response. No new packages, MIDI or files.
"""
from __future__ import annotations

from array import array
import math
import statistics
import sys

NOTE_GESTURES = {
    "answer-fifth": 7,
    "answer-third": 4,
    "answer-below": -5,
    "answer-octave": 12,
}


def render_note_reply(features: dict, gesture: str) -> tuple[bytes, list[int]]:
    """Render conservative dual-mono PCM16 and MIDI notes, or silence if no pitch.

    Notes are deliberately sparse, played on alternate supplied beat slots.
    Melody uses a *rough* pitch hint and short fixed contours, not a chord/key
    inference or neural synthesis. Fail closed on unrecognized model decisions.
    """
    if gesture not in NOTE_GESTURES:
        raise ValueError("unrecognized note gesture")
    rate = features["sample_rate"]
    frames = features["frames"]
    channels = features["channels"]
    slots = features["slices"]
    if rate not in (44100, 48000) or channels not in (1, 2):
        raise ValueError("unsupported note reply audio format")
    if not 0 < frames <= rate * 8 or not 1 <= len(slots) <= 16:
        raise ValueError("note reply must be between 1 and 8 seconds")
    notes = features.get("musical", {}).get("pitch_hints", [])
    reliable = [
        hint["midi_note"] for hint in notes
        if isinstance(hint.get("midi_note"), int)
        and 36 <= hint["midi_note"] <= 84
        and hint.get("confidence", 0) >= .85
    ]
    output = array("h", [0]) * (frames * 2)
    if not reliable:
        if sys.byteorder != "little":
            output.byteswap()
        return output.tobytes(), []

    base = round(statistics.median(reliable))
    interval = NOTE_GESTURES[gesture]
    answer_notes = []
    contour = (0, 2, -2, 0)
    for i in range(1, len(slots), 2):
        slot = slots[i]
        start = slot["start_frame"]
        count = min(slot["frames"], frames - start)
        # Short notes and rests leave room for the musician's lead.
        count = min(count, round(rate * .35))
        if count <= 0:
            continue
        pitch = max(48, min(84, base + interval + contour[len(answer_notes) % len(contour)]))
        answer_notes.append(pitch)
        hz = 440.0 * 2 ** ((pitch - 69) / 12)
        fade = max(1, round(rate * .015))
        for n in range(count):
            envelope = min(1.0, n / fade, (count - 1 - n) / fade)
            # Low-level, slightly rounded timbre; peak <6% of full scale.
            phase = 2 * math.pi * hz * n / rate
            sample = round(32767 * envelope *
                           (.045 * math.sin(phase) + .007 * math.sin(2 * phase)))
            position = 2 * (start + n)
            output[position] = sample
            output[position + 1] = sample
    if sys.byteorder != "little":
        output.byteswap()
    return output.tobytes(), answer_notes


def mix_note_reply(source: bytes, notes: bytes, *, source_gain: float = .5) -> bytes:
    """Mix a reduced recorded voice with generated notes; hard cap at -6 dBFS.

    Both streams are already stereo signed PCM16. Work happens before playback,
    never in the PortAudio callback; don't raise the live microphone level.
    """
    if not source or len(source) != len(notes) or len(source) % 4:
        raise ValueError("note reply buffers must be nonempty, equal stereo PCM16")
    if not 0 <= source_gain <= 1:
        raise ValueError("source gain must be between 0 and 1")
    original = array("h")
    original.frombytes(source)
    synthetic = array("h")
    synthetic.frombytes(notes)
    if sys.byteorder != "little":
        original.byteswap()
        synthetic.byteswap()
    ceiling = round(32767 * .5)
    for i, voice in enumerate(original):
        value = round(voice * source_gain + synthetic[i])
        original[i] = max(-ceiling, min(ceiling, value))
    if sys.byteorder != "little":
        original.byteswap()
    return original.tobytes()
