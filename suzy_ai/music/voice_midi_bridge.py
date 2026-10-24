"""Experimental: Scarlett monophonic voice -> CoreMIDI note control for AI instruments.

This is NOT speech/beat listening or AI by itself. A downstream local
MIDI-conditioned model (e.g. MRT2 Small) supplies neural music generation.
No files, Qwen, cloud, MIDI clock, audio passthrough or automatic Logic edits.
"""
from __future__ import annotations

from array import array
from dataclasses import dataclass
from queue import Empty, Full, Queue
import argparse
import math
import sys
import time

from .phrase import _pitch

RATE = 48000
WINDOW = round(RATE * .045)
HOP = 2048  # 42.7ms at 48 kHz; pitch estimate is approximate.


@dataclass
class NoteGate:
    """Debounce noisy monophonic note guesses and ALWAYS release on silence."""
    channel: int = 1
    transpose: int = 0
    min_confidence: float = .86
    min_rms: float = .012
    stable_frames: int = 2
    silent_frames: int = 3

    def __post_init__(self):
        if (type(self.channel) is not int or not 1 <= self.channel <= 16
                or type(self.transpose) is not int or not -24 <= self.transpose <= 24
                or not 0.84 <= self.min_confidence <= 1.0
                or not 0.0 < self.min_rms <= .5
                or not 1 <= self.stable_frames <= 8
                or not 1 <= self.silent_frames <= 10):
            raise ValueError("invalid microphone-to-MIDI safety settings")
        self.active = None
        self.candidate = None
        self.candidate_count = 0
        self.misses = 0

    def observe(self, pitch, confidence, rms):
        """Return ordinary MIDI status/data triplets. No disk or hardware here."""
        confidence = float(confidence)
        rms = float(rms)
        if (not math.isfinite(confidence) or not math.isfinite(rms)
                or pitch is not None and (type(pitch) is not int or not 36 <= pitch <= 84)):
            pitch = None
        if confidence < self.min_confidence or rms < self.min_rms:
            pitch = None
        if pitch is not None:
            pitch += self.transpose
            if not 24 <= pitch <= 108:
                pitch = None
        if pitch is None:
            self.candidate = None
            self.candidate_count = 0
            self.misses += 1
            if self.active is not None and self.misses >= self.silent_frames:
                old = self.active
                self.active = None
                return [[0x80 + self.channel - 1, old, 0]]
            return []
        self.misses = 0
        if pitch == self.active:
            self.candidate = None
            self.candidate_count = 0
            return []
        if pitch == self.candidate:
            self.candidate_count += 1
        else:
            self.candidate = pitch
            self.candidate_count = 1
        if self.candidate_count < self.stable_frames:
            return []
        midi = []
        if self.active is not None:
            midi.append([0x80 + self.channel - 1, self.active, 0])
        self.active = pitch
        self.candidate = None
        self.candidate_count = 0
        # Conservative fixed velocity: measured mic loudness is not calibrated.
        midi.append([0x90 + self.channel - 1, pitch, 65])
        return midi

    def panic(self):
        messages = []
        if self.active is not None:
            messages.append([0x80 + self.channel - 1, self.active, 0])
        messages += [[0xB0 + self.channel - 1, 123, 0],
                     [0xB0 + self.channel - 1, 120, 0]]
        self.active = self.candidate = None
        self.candidate_count = self.misses = 0
        return messages


def estimated_pitch(pcm: bytes, *, channels: int, mic_channel: int):
    """Pitch inference off audio callback, from the last ~45ms of dry mic PCM."""
    if (channels not in (1, 2) or mic_channel not in (1, 2)
            or mic_channel > channels or len(pcm) % (2 * channels)):
        raise ValueError("invalid interleaved microphone samples")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    mono = samples[mic_channel-1::channels]
    if len(mono) < WINDOW:
        return None, 0.0, 0.0
    # The project's existing conservative pitch estimator expects ~8 kHz.
    # Sixfold decimation needs anti-alias filtering for production use;
    # this rehearsal-only probe assumes dry, clean monophonic input.
    tail = mono[-WINDOW:]
    values = [v / 32768.0 for v in tail[::6]]
    return _pitch(values, RATE / 6)


def choose_device(devices, requested, field):
    matches = [(i, item) for i, item in enumerate(devices)
               if item.get("max_input_channels", 0) >= 1]
    if not matches:
        raise ValueError("no microphone capture input found")
    if requested.isdecimal():
        index = int(requested)
        if index not in {i for i, _ in matches}:
            raise ValueError(f"{field} is not a microphone input device")
        return index
    matches = [(i, item) for i, item in matches
               if requested.casefold() in item["name"].casefold()]
    if len(matches) != 1:
        raise ValueError(
            f"{field}: expected one matching microphone input; found {len(matches)}. "
            "Use --list-devices and pass an exact index.")
    return matches[0][0]


def choose_midi_port(ports, requested):
    if requested.isdecimal():
        index = int(requested)
        if 0 <= index < len(ports):
            return index
        raise ValueError("MIDI output port index not found")
    matches = [i for i, name in enumerate(ports)
               if requested.casefold() in name.casefold()]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one MIDI port matching {requested!r}; "
            f"found {len(matches)}. List devices and use its index.")
    return matches[0]


def main():
    parser = argparse.ArgumentParser(
        description="Experimental monophonic voice to MIDI for LOCAL audio-generating AI")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--input-device", default="Scarlett")
    parser.add_argument("--input-channel", type=int, default=1, choices=(1,2))
    parser.add_argument("--midi-output", help="Choose an existing output (e.g. Magenta RT Input or IAC Driver Bus 1)")
    parser.add_argument("--midi-channel", type=int, default=1)
    parser.add_argument("--transpose", type=int, default=0)
    parser.add_argument("--confidence", type=float, default=.86)
    parser.add_argument("--min-rms", type=float, default=.012)
    args=parser.parse_args()
    try:
        import sounddevice as sd
        import rtmidi
    except ImportError:
        parser.error('Install optional dependencies: .venv-mac/bin/python -m pip install -e ".[live-midi]"')
    midi=rtmidi.MidiOut()
    devices=sd.query_devices()
    ports=midi.get_ports()
    if args.list_devices:
        print("Audio inputs:")
        for i, device in enumerate(devices):
            if device["max_input_channels"]:
                print(f"  {i}: {device['name']} (inputs: {device['max_input_channels']})")
        print("MIDI outputs:")
        for i, name in enumerate(ports):
            print(f"  {i}: {name}")
        return
    if not args.midi_output:
        parser.error("Explicit --midi-output is required; refusing to send notes to an arbitrary MIDI destination")
    index = choose_device(devices, args.input_device, "--input-device")
    channels = min(2, int(devices[index]["max_input_channels"]))
    if args.input_channel > channels:
        parser.error("the selected input has fewer physical mic channels")
    port = choose_midi_port(ports, args.midi_output)
    gate = NoteGate(channel=args.midi_channel, transpose=args.transpose,
                    min_confidence=args.confidence, min_rms=args.min_rms)
    fifo = Queue(maxsize=6)
    def callback(indata, frames, time_info, status):
        # No model, MIDI driver, disk or network call from PortAudio callback.
        data = bytes(indata)
        try:
            fifo.put_nowait(data)
        except Full:
            # On overload, drop frames rather than block the audio thread.
            pass
    print("Experimental voice->MIDI; no recording or network. Dry vocals work best.")
    print(f"Scarlett input {index} / channel {args.input_channel} -> CoreMIDI: {ports[port]}")
    print("Play softly at first. Controller sends at most one held pitch at a time.")
    print("Ctrl-C -> explicit Note Off + All Notes Off + All Sound Off.")
    try:
        midi.open_port(port)
        with sd.RawInputStream(device=index,channels=channels,samplerate=RATE,
                               dtype="int16",blocksize=HOP,callback=callback):
            collected=bytearray()
            last_activity=time.monotonic()
            while True:
                try:
                    chunk=fifo.get(timeout=.12)
                except Empty:
                    # If microphone driver stops delivering, release held notes.
                    if time.monotonic() - last_activity > .2:
                        for message in gate.observe(None,0,0):
                            midi.send_message(message)
                    continue
                last_activity=time.monotonic()
                collected.extend(chunk)
                max_bytes=WINDOW*channels*2
                if len(collected) < max_bytes:
                    continue
                captured = bytes(collected[-max_bytes:])
                collected.clear()
                pitch, confidence, rms=estimated_pitch(
                    captured,channels=channels,mic_channel=args.input_channel)
                for message in gate.observe(pitch,confidence,rms):
                    midi.send_message(message)
    except KeyboardInterrupt:
        print("Stopping microphone-to-MIDI bridge.")
    finally:
        if midi.is_port_open():
            for message in gate.panic():
                midi.send_message(message)
            midi.close_port()


if __name__ == "__main__":
    main()
