"""Lifecycle/IPC for one native MRT2 Audio Unit host, never a simulated model.

The native subprocess hosts exactly one Google AU and sends JSON status over
stdin/stdout. Starting the browser alone does not start the MLX model. The
native helper is opt-in and must be built with scripts/build-toaster-magenta.sh.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import select
import subprocess
from threading import RLock

ROOT = Path(__file__).resolve().parents[2]
EXECUTABLE = ROOT / ".build" / "toaster-magenta-host"
ACTIONS = {
    "start": frozenset(),
    "stop": frozenset(),
    "status": frozenset(),
    "scene": frozenset({"scene"}),
    "mix": frozenset({"value"}),
    "volume": frozenset({"value"}),
    "reverb": frozenset({"value"}),
    "mute": frozenset({"value"}),
    "chord": frozenset({"index"}),
    "tempo": frozenset({"bpm"}),
    "note": frozenset({"note"}),
    "note-off": frozenset({"note"}),
    "release": frozenset(),
}
PROMPTS = {
    "pyramid": "Intimate warm piano chords, fragile orchestral strings, sparse melancholic experimental art rock, slow floating asymmetric pulse, soft bass, subtle ambient textures, restrained percussion, no vocals",
    "fishes": "Interlocking clean guitar arpeggios, shimmering echoes, hypnotic experimental art rock, flowing bass, understated drums, glassy synthesizers, gradually building ethereal atmosphere, no vocals",
}


class NativeMagentaHost:
    def __init__(self, binary=EXECUTABLE):
        self.binary = Path(binary)
        self.process = None
        self.lock = RLock()
        self.log = None

    def status(self):
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                return {
                    "phase": "not-running",
                    "native_au": False,
                    "model_audio_confirmed": False,
                    "build_available": self.binary.is_file(),
                    "prompts": PROMPTS,
                    "message": "Google MRT2 not started. Browser audio still works.",
                }
            return self._request({"op": "status"})

    def _start(self):
        if self.process is not None and self.process.poll() is None:
            return
        if platform.system() != "Darwin":
            raise RuntimeError("Native Magenta Audio Unit requires macOS")
        if not self.binary.is_file():
            raise RuntimeError("Native Magenta host not built. Run bash scripts/build-toaster-magenta.sh")
        self.binary.parent.mkdir(parents=True, exist_ok=True)
        self.log = open(self.binary.parent / "toaster-magenta-stderr.log", "ab", buffering=0)
        self.process = subprocess.Popen(
            [str(self.binary)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.log, cwd=ROOT, bufsize=1, text=True,
            env=os.environ.copy(),
        )

    def _request(self, payload):
        process = self.process
        if process is None or process.poll() is not None:
            raise RuntimeError("MRT2 native host not running")
        try:
            process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            process.stdin.flush()
            ready, _, _ = select.select([process.stdout], [], [], 4.0)
            if not ready:
                raise RuntimeError("MRT2 host timeout. Check .build/toaster-magenta-stderr.log")
            line = process.stdout.readline()
            if not line:
                raise RuntimeError("MRT2 host exited. Check .build/toaster-magenta-stderr.log")
            result = json.loads(line)
            if not isinstance(result, dict):
                raise RuntimeError("Malformed MRT2 host response")
            return result
        except (OSError, ValueError) as exc:
            raise RuntimeError("MRT2 host communication error") from exc

    def command(self, action, data):
        with self.lock:
            if action not in ACTIONS or not isinstance(data, dict):
                raise ValueError("unknown AI action")
            if set(data) != ACTIONS[action]:
                raise ValueError("invalid AI action fields")
            if action == "scene":
                if type(data["scene"]) is not str or data["scene"] not in PROMPTS:
                    raise ValueError("scene must be pyramid or fishes")
            if action in ("mix", "volume", "reverb"):
                v = data["value"]
                if type(v) not in (int, float) or not 0 <= v <= 1:
                    raise ValueError("value must be 0..1")
            if action == "mute" and type(data["value"]) is not bool:
                raise ValueError("mute must be true or false")
            if action == "chord" and (type(data["index"]) is not int or not 0 <= data["index"] < 4):
                raise ValueError("chord must be integer 0..3")
            if action == "tempo":
                bpm = data["bpm"]
                if type(bpm) not in (int, float) or not 60 <= bpm <= 190:
                    raise ValueError("tempo must be 60..190 BPM")
            if action in ("note", "note-off"):
                note = data["note"]
                if type(note) is not int or not 0 <= note <= 127:
                    raise ValueError("note must be MIDI integer 0..127")
            if action == "start":
                self._start()
            elif self.process is None or self.process.poll() is not None:
                if action == "stop":
                    return self.status()
                raise RuntimeError("MRT2 not running: press ENABLE MAGENTA first")
            return self._request({"op": action, **data})

    def close(self):
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                try:
                    self._request({"op": "stop"})
                except RuntimeError:
                    pass
                try:
                    self.process.stdin.close()
                    self.process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    self.process.terminate()
            self.process = None
            if self.log:
                self.log.close()
                self.log = None
