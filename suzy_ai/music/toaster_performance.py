"""Deterministic, computer-keyboard-driven MIDI for the existing Magenta bridge.

This is deliberately a small symbolic *conditioner*: the hosted Magenta engine
owns audio. No LLM, model prompt control, CoreAudio, Logic transport or audio
mute is simulated here. The groove uses a monotonic clock, not Logic sync.
"""
from __future__ import annotations

from threading import Event, RLock, Thread
import time

CHORDS = {
    "pyramid": (
        ("F♯", (54, 58, 61, 66)),
        ("Gmaj7", (55, 59, 62, 66)),
        ("A6", (57, 61, 64, 66)),
        ("F♯ · home", (54, 58, 61, 66)),
    ),
    "fishes": (
        ("Em7", (52, 55, 59, 62)),
        ("F♯m7", (54, 57, 61, 64)),
        ("A", (57, 61, 64, 69)),
        ("Gmaj7", (55, 59, 62, 66)),
    ),
}
RHYTHMS = ("float", "pulse", "arpeggio", "off")
# Four chord pads are deliberately mapped to 1–4, not the Keystation.
# In Pyramid the full five-accent form is played 1→2→3→2→4 manually.


class ToasterPerformance:
    def __init__(self, bridge):
        self.bridge = bridge
        self.lock = RLock()
        self.scene = "pyramid"
        self.bpm = 105
        self.rhythm = "float"
        self.intensity = 55
        self.index = None
        self.chord_notes = ()
        self.groove_note = None
        self.step = 0
        self.running = False
        self.stop_signal = Event()
        self.worker = None

    def _note(self, channel, note, velocity):
        # Match the bridge's proven /api/test format: MIDI CHANNEL ONE (status
        # 0x90 / 0x80). The first live build used channels 2 and 3 and Jam may
        # ignore them. Keep musical chord and groove independent by shifting
        # the groove voice an octave, rather than separating MIDI channels.
        channel = 0
        # Bridge's MIDI output requires the same mutex as the hardware callback.
        with self.bridge.lock:
            if self.bridge.closed:
                if velocity:
                    raise ValueError("MIDI bridge closed")
                return  # Graceful shutdown if the host closed before cleanup.
            self.bridge._send([0x90 | channel if velocity else 0x80 | channel, note, velocity])

    def _silence(self):
        for n in self.chord_notes:
            self._note(1, n, 0)
        self.chord_notes = ()
        if self.groove_note is not None:
            self._note(2, self.groove_note, 0)
            self.groove_note = None

    def status(self):
        with self.lock:
            return {
                "scene": self.scene, "bpm": self.bpm, "rhythm": self.rhythm,
                "intensity": self.intensity, "chord_index": self.index,
                "chords": [name for name, _ in CHORDS[self.scene]],
                "running": self.running, "step": self.step,
                "virtual_source": "SUZY AI MIDI",
                "midi_channel": 1,
                "magenta_audio_confirmed": False,
                "clock": "independent_monotonic_not_logic_synced",
                "message": "MIDI output only. Silence neural audio in Magenta or Logic.",
            }

    def _halt(self):
        self.running = False
        self.stop_signal.set()
        self._silence()
        self.index = None

    def scene_change(self, scene):
        if type(scene) is not str or scene not in CHORDS:
            raise ValueError("scene must be pyramid or fishes")
        with self.lock:
            self._halt()
            self.scene = scene
            self.bpm = 105 if scene == "pyramid" else 153
            self.rhythm = "float" if scene == "pyramid" else "arpeggio"
            self.step = 0
            return self.status()

    def chord(self, index):
        if type(index) is not int or not 0 <= index < 4:
            raise ValueError("chord pad must be 0..3")
        with self.lock:
            if not self.bridge.gate_open:
                raise ValueError("resume MIDI first")
            if self.bridge.closed:
                raise ValueError("MIDI bridge closed")
            # Switching harmonies releases *only* this performance channel.
            self._silence()
            self.index = index
            notes = CHORDS[self.scene][index][1]
            self.chord_notes = notes
            velocity = max(24, min(95, int(30 + self.intensity * 0.48)))
            for n in notes:
                self._note(1, n, velocity)
            return self.status()

    def settings(self, *, bpm, rhythm, intensity):
        if type(bpm) is not int or not 60 <= bpm <= 190:
            raise ValueError("BPM must be integer 60..190")
        if type(rhythm) is not str or rhythm not in RHYTHMS:
            raise ValueError("invalid rhythm")
        if type(intensity) is not int or not 0 <= intensity <= 100:
            raise ValueError("intensity must be integer 0..100")
        with self.lock:
            self.bpm, self.rhythm, self.intensity = bpm, rhythm, intensity
            if rhythm == "off":
                self.running = False
                self.stop_signal.set()
                if self.groove_note is not None:
                    self._note(2, self.groove_note, 0)
                    self.groove_note = None
            return self.status()

    def start(self):
        with self.lock:
            if not self.bridge.gate_open:
                raise ValueError("resume MIDI first")
            if self.bridge.closed:
                raise ValueError("MIDI bridge closed")
            if self.rhythm == "off":
                raise ValueError("choose a rhythm first")
            if self.index is None:
                raise ValueError("press a chord pad before starting the rhythm")
            if self.running:
                return self.status()
            self.stop_signal = Event()
            self.running = True
            self.step = 0
            self.worker = Thread(target=self._clock, args=(self.stop_signal,), daemon=True)
            self.worker.start()
            return self.status()

    def stop(self):
        with self.lock:
            self._halt()
            return self.status()

    def _clock(self, signal):
        """Independent half-beat MIDI rhythm. Bounded jitter; never promise DAW sync."""
        deadline = time.monotonic()
        try:
            while not signal.is_set():
                with self.lock:
                    if not self.running or self.index is None or not self.bridge.gate_open:
                        break
                    if self.groove_note is not None:
                        self._note(2, self.groove_note, 0)
                        self.groove_note = None
                    s = self.step
                    voices = CHORDS[self.scene][self.index][1]
                    if self.rhythm == "float":
                        # PYRAMID accent cycle: 3+3+4+3+3 eighth notes.
                        active = s % 16 in (0, 3, 6, 10, 13)
                        note = voices[(s // 3) % len(voices)]
                    elif self.rhythm == "pulse":
                        active = s % 2 == 0
                        note = voices[(s // 2) % len(voices)]
                    elif self.rhythm == "arpeggio":
                        active = True
                        note = voices[1 + (s % (len(voices) - 1))]
                    else:
                        active = False
                        note = voices[0]
                    if active:
                        velocity = max(18, min(115, int(28 + 0.7 * self.intensity)))
                        note += 12  # Groove is a distinct upper voice, avoids off/on chord overlap.
                        self._note(2, note, velocity)
                        self.groove_note = note
                    self.step += 1
                    interval = 30.0 / self.bpm
                deadline += interval
                delay = deadline - time.monotonic()
                if delay <= -interval * 2:
                    deadline = time.monotonic()
                elif signal.wait(max(0, delay)):
                    break
        finally:
            with self.lock:
                # A stale thread from a previous START must not silence new notes.
                if self.stop_signal is signal:
                    self.running = False
                    if self.groove_note is not None:
                        self._note(2, self.groove_note, 0)
                        self.groove_note = None

    def close(self):
        self.stop()
