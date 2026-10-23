"""Model-directed sampled-vocal replies in a bounded stereo PCM buffer.

This preserves the performer's recorded timbre. It is *not* a neural voice
cloner and cannot invent new lyrics or a new sung melody. Qwen selects a
gesture, while offline DSP arranges the actual source waveform as a layer.
"""
from array import array
import math
import sys

VOCAL_GESTURES = frozenset(("vocal-canon", "vocal-echo", "vocal-stutter", "vocal-reverse"))


def render_vocal_layer(pcm: bytes, features: dict, gesture: str) -> bytes:
    """Rearrange actual recorded vocal samples in time; return dual-stereo PCM16.

    Input must be exactly the described 44.1/48k stereo phrase. Only reads audio
    and writes a new buffer off the PortAudio thread. No model/sample IO inside
    the real-time audio callback. Silence occupies gaps intentionally.
    """
    if gesture not in VOCAL_GESTURES:
        raise ValueError("unrecognized vocal response gesture")
    rate = features["sample_rate"]
    frames = features["frames"]
    channels = features["channels"]
    slots = features["slices"]
    if rate not in (44100, 48000) or channels != 2:
        raise ValueError("vocal response requires 44.1/48k stereo PCM16")
    if (not 0 < frames <= rate * 8 or not 1 <= len(slots) <= 16
            or len(pcm) != frames * 4):
        raise ValueError("vocal response input does not match measured phrase")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    result = array("h", [0]) * (frames * 2)
    beat = max(1, round(rate * 60 / features["bpm_supplied"]))
    fade = max(1, round(rate * .012))

    def add_fragment(source: int, destination: int, length: int, *, reverse=False):
        if source < 0 or destination < 0 or source + length > frames or destination + length > frames:
            raise ValueError("vocal sample fragment out of range")
        for n in range(length):
            index = length - 1 - n if reverse else n
            # Gentle fades avoid sharp speech edit clicks.
            envelope = min(1.0, n / fade, (length - 1 - n) / fade)
            for channel in range(2):
                raw = samples[(source + index) * 2 + channel]
                loc = (destination + n) * 2 + channel
                mixed = result[loc] + round(raw * envelope * .58)
                result[loc] = max(-16384, min(16384, mixed))

    if gesture in ("vocal-canon", "vocal-echo"):
        # One- or two-beat delayed real-voice canon. Some tail is
        # intentionally truncated, so a complete new voice phrase is NOT invented.
        delay = beat if gesture == "vocal-canon" else beat * 2
        if delay < frames:
            add_fragment(0, delay, frames - delay)
    elif gesture == "vocal-stutter":
        # Echo the first half of each beat twice, leaving rhythmic gaps.
        for slot in slots:
            start = slot["start_frame"]
            length = min(slot["frames"], frames - start)
            grain = min(length // 2, round(rate * .22))
            if grain > fade * 2 and start + grain * 2 <= frames:
                add_fragment(start, start, grain)
                add_fragment(start, start + grain, grain)
    else:  # vocal-reverse
        # Rewind each beat in place for recognizable but audibly altered texture.
        for slot in slots:
            start = slot["start_frame"]
            length = min(slot["frames"], frames - start)
            if length > fade * 2:
                add_fragment(start, start, length, reverse=True)
    if sys.byteorder != "little":
        result.byteswap()
    return result.tobytes()


def cultural_voice_stems(source: bytes, layer: bytes, role: str) -> dict[str, bytes]:
    """Apply the model's *mix role* to the sampled voice, off callback.

    This is a mix/dynamic choice, NOT newly composed counterpoint or
    an artist voice imitation. The isolated previews exactly match
    their contribution to the final stereo duet.
    """
    from .culture import VOCAL_ROLES
    if role not in VOCAL_ROLES:
        raise ValueError("unknown cultural vocal role")
    if not source or len(source) != len(layer) or len(source) % 4:
        raise ValueError("cultural voice stems require equal stereo PCM16")
    source_gain, layer_gain = VOCAL_ROLES[role]
    s = array("h")
    t = array("h")
    s.frombytes(source)
    t.frombytes(layer)
    if sys.byteorder != "little":
        s.byteswap()
        t.byteswap()
    original, isolated, duet = array("h"), array("h"), array("h")
    limit = round(32767 * .5)
    for a, b in zip(s, t):
        dry = round(a * source_gain)
        wet = round(b * layer_gain)
        original.append(dry)
        isolated.append(wet)
        duet.append(max(-limit, min(limit, dry + wet)))
    if sys.byteorder != "little":
        original.byteswap()
        isolated.byteswap()
        duet.byteswap()
    return {"original": original.tobytes(), "layer": isolated.tobytes(),
            "duet": duet.tobytes()}
