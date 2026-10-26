"""Opt-in CoreMIDI steering for external neural instruments such as MRT2 Jam.

Creates a virtual MIDI *source* visible to other macOS MIDI input applications.
No audio routing, model inference, Logic control, Qwen, or DAW mute claims.
"""
from __future__ import annotations

from threading import RLock, Timer
import time

VIRTUAL_PORT = "SUZY AI MIDI"
MODES = {"direct": 0, "low": -12, "high": 12}
TEST_CHORD = (57, 60, 64, 67)  # A minor seventh, MIDI 1 channel


class MagentaMidiBridge:
    def __init__(self, rtmidi):
        self.rtmidi = rtmidi
        self.lock = RLock()
        self.output = rtmidi.MidiOut()
        self.output.open_virtual_port(VIRTUAL_PORT)
        self.source = None
        self.source_name = None
        self.mode = "direct"
        self.held = {}
        self.gate_open = True
        self.test_notes = ()
        self.test_timer = None
        self.forwarded = 0
        self.last_event = None
        self.closed = False

    def inputs(self):
        midi = self.rtmidi.MidiIn()
        try:
            return [str(p) for p in midi.get_ports()
                    if VIRTUAL_PORT.casefold() not in str(p).casefold()]
        finally:
            del midi

    def status(self):
        with self.lock:
            return {
                "enabled": not self.closed,
                "virtual_source": VIRTUAL_PORT,
                "input_name": self.source_name,
                "mode": self.mode,
                "gate_open": self.gate_open,
                "held_notes": len(self.held) + len(self.test_notes),
                "midi_events_forwarded": self.forwarded,
                "last_midi_seconds_ago": round(time.monotonic() - self.last_event, 1)
                    if self.last_event is not None else None,
                "magenta_connection": "not_observed",
                "ai_audio_muted": "not_observed",
                "message": "MIDI steering only. Release MIDI is NOT an audio mute.",
            }

    def _send(self, message):
        self.output.send_message(message)
        self.forwarded += 1
        self.last_event = time.monotonic()

    def _release_locked(self):
        if self.test_timer:
            self.test_timer.cancel()
            self.test_timer = None
        for (ch, _src), dest in tuple(self.held.items()):
            self._send([0x80 | ch, dest, 0])
        self.held.clear()
        for note in self.test_notes:
            self._send([0x80, note, 0])
        self.test_notes = ()
        # Clear sustain and hanging note states on all channels, without claiming
        # a streaming neural audio engine will become silent.
        for ch in range(16):
            self._send([0xB0 | ch, 64, 0])
            self._send([0xB0 | ch, 123, 0])
            self._send([0xB0 | ch, 120, 0])

    def release(self):
        with self.lock:
            if self.closed:
                raise ValueError("MIDI bridge is closed")
            self._release_locked()
            return self.status()

    def change_mode(self, mode):
        if type(mode) is not str or mode not in MODES:
            raise ValueError("choose direct, low or high")
        with self.lock:
            if self.closed:
                raise ValueError("MIDI bridge is closed")
            if self.mode != mode:
                self._release_locked()
                self.mode = mode
            return self.status()

    def connect(self, exact_name):
        if type(exact_name) is not str or not exact_name.strip():
            raise ValueError("choose an exact MIDI input")
        with self.lock:
            if self.closed:
                raise ValueError("MIDI bridge is closed")
            candidate = self.rtmidi.MidiIn()
            names = candidate.get_ports()
            matches = [i for i, name in enumerate(names) if name == exact_name
                       and VIRTUAL_PORT.casefold() not in name.casefold()]
            if len(matches) != 1:
                raise ValueError("MIDI input missing or ambiguous; refresh ports")
            # Build and validate new input BEFORE retiring a working connection.
            candidate.ignore_types(sysex=True, timing=True, active_sense=True)
            candidate.open_port(matches[0])
            candidate.set_callback(self._receive)
            self._release_locked()
            old = self.source
            self.source = candidate
            self.source_name = exact_name
            if old is not None:
                old.close_port()
            return self.status()

    def _receive(self, event, data=None):
        """Small, deterministic MIDI input callback. Never invokes a model."""
        message = event[0] if event else ()
        if len(message) < 3:
            return
        status, note, velocity = [int(v) for v in message[:3]]
        command, ch = status & 0xF0, status & 0x0F
        if command not in (0x80, 0x90) or not 0 <= note < 128:
            return
        with self.lock:
            if self.closed or self.source is None or not self.gate_open:
                return
            key = ch, note
            is_on = command == 0x90 and velocity > 0
            old_note = self.held.pop(key, None)
            if old_note is not None:
                self._send([0x80 | ch, old_note, 0])
            if is_on:
                target = note + MODES[self.mode]
                if 0 <= target < 128:
                    self._send([0x90 | ch, target, max(1, min(127, velocity))])
                    self.held[key] = target

    def set_gate(self, enabled):
        if type(enabled) is not bool:
            raise ValueError("enabled must be true or false")
        with self.lock:
            if self.closed:
                raise ValueError("MIDI bridge is closed")
            if not enabled and self.gate_open:
                self._release_locked()
            self.gate_open = enabled
            return self.status()

    def disconnect(self):
        with self.lock:
            if self.closed:
                raise ValueError("MIDI bridge is closed")
            self._release_locked()
            if self.source is not None:
                self.source.close_port()
                self.source = None
            self.source_name = None
            return self.status()

    def test_chord(self):
        """One short MIDI conditioning chord, automatically released."""
        with self.lock:
            if self.closed:
                raise ValueError("MIDI bridge is closed")
            if not self.gate_open:
                raise ValueError("resume MIDI before sending a test chord")
            if self.held or self.test_notes:
                raise ValueError("release keyboard notes before the test chord")
            notes = tuple(note + MODES[self.mode] for note in TEST_CHORD)
            if not all(0 <= n < 128 for n in notes):
                raise ValueError("test chord outside MIDI range")
            self.test_notes = notes
            for note in notes:
                self._send([0x90, note, 48])
            self.test_timer = Timer(0.8, self._finish_test)
            self.test_timer.daemon = True
            self.test_timer.start()
            return self.status()

    def _finish_test(self):
        with self.lock:
            for note in self.test_notes:
                self._send([0x80, note, 0])
            self.test_notes = ()
            self.test_timer = None

    def close(self):
        with self.lock:
            if self.closed:
                return
            self._release_locked()
            self.closed = True
            if self.source:
                self.source.close_port()
                self.source = None
            self.source_name = None
            self.output.close_port()
