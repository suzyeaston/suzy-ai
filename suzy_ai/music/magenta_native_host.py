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
from threading import RLock, Thread

ROOT = Path(__file__).resolve().parents[2]
EXECUTABLE = ROOT / ".build" / "toaster-magenta-host"
ACTIONS = {
    "start": frozenset(),
    "stop": frozenset(),
    "status": frozenset(),
    "show-au-ui": frozenset(),
    "transport-play": frozenset(),
    "transport-pause": frozenset(),
    "scene": frozenset({"scene"}),
    "configure-prompts": frozenset({"prompts"}),
    "mix": frozenset({"value"}),
    "lead-mix": frozenset({"scene", "value"}),
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
    "pyramid_violin": "Expressive solo bowed violin, rich warm acoustic strings, intimate chamber texture, lyrical sustained legato phrases, delicate vibrato, subtle bow noise, suspended melancholy, no piano, no guitar, no vocals",
    "fishes_guitar": "Expressive nylon-string classical guitar, intricate fingerpicked melodic arpeggios, warm wooden resonance, soft plucked string attacks, interlocking counterpoint, clear intimate acoustic guitar, no piano, no violin, no vocals",
}


class NativeMagentaHost:
    def __init__(self, binary=EXECUTABLE):
        self.binary = Path(binary)
        self.process = None
        self.lock = RLock()
        self.log = None
        self.launching = False
        self.launch_error = ""
        self.closing = False

    def launch_async(self):
        """App launch starts ONE native Magenta instance off the HTTP thread.

        Never start from import or from a web page refresh. If a binary is
        missing, compile the local source using the fixed Swift/SDK selector.
        """
        with self.lock:
            if self.launching or self.closing:
                return
            if self.process is not None and self.process.poll() is None:
                return
            self.launching = True
            self.launch_error = ""
            Thread(target=self._launch_worker, name="toaster-magenta-start", daemon=True).start()

    @staticmethod
    def _register_installed_au(app_paths=None):
        """Best-effort registration of Google's actual AUv3 extension.

        Jam and Collider are independent applications: neither is an AU.
        Only touch an existing MRT2 (AU).app at a permanent Applications path.
        No downloading, deleting stale extensions, or registrar process killing.
        """
        candidates = app_paths if app_paths is not None else [
            Path.home() / "Applications" / "MRT2 (AU).app",
            Path("/Applications/MRT2 (AU).app"),
        ]
        for app in candidates:
            extension = Path(app) / "Contents/PlugIns/MRT2_AU.appex"
            if not extension.is_dir():
                continue
            try:
                result = subprocess.run(
                    ["pluginkit", "-a", str(extension)],
                    capture_output=True, text=True, timeout=12, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise RuntimeError(
                    "MRT2 (AU).app was found, but its AUv3 extension could not be registered: "
                    + str(exc)[:180]
                ) from exc
            if result.returncode != 0:
                raise RuntimeError(
                    "macOS pluginkit could not register MRT2_AU.appex. "
                    "Open MRT2 (AU).app once and restart TOASTER. "
                    + (result.stderr or result.stdout)[-240:]
                )
            return str(app)
        return None

    def _launch_worker(self):
        error = ""
        try:
            if platform.system() != "Darwin":
                raise RuntimeError("Magenta native audio requires macOS")
            source = ROOT / "apps/toaster-magenta/ToasterMagentaHost.swift"
            stale = (not self.binary.is_file()
                     or (source.is_file() and source.stat().st_mtime_ns > self.binary.stat().st_mtime_ns))
            if stale:
                if self.binary != EXECUTABLE:
                    raise RuntimeError("Native host executable not present")
                build = subprocess.run(
                    ["bash", str(ROOT / "scripts/build-toaster-magenta.sh")],
                    cwd=ROOT, timeout=180, capture_output=True, text=True,
                )
                if build.returncode != 0:
                    raise RuntimeError(
                        "Native helper build failed: " + (build.stdout + build.stderr)[-450:]
                    )
            # If the official AU app is already installed, register its
            # embedded extension *before* starting our fresh host process.
            # AVAudioUnitComponentManager then sees the newly registered AU.
            self._register_installed_au()
            with self.lock:
                if self.closing:
                    return
                self._start()
                response = self._request({"op": "start"})
                if response.get("error"):
                    raise RuntimeError(str(response["error"]))
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            error = str(exc)[:600]
        finally:
            with self.lock:
                self.launching = False
                self.launch_error = error

    def _inactive_status(self):
        return {
            "phase": "starting" if self.launching else "failed" if self.launch_error else "not-running",
            "native_au": False,
            "model_audio_confirmed": False,
            "build_available": self.binary.is_file(),
            "prompts": PROMPTS,
            "error": self.launch_error,
            "message": "Starting Magenta automatically…" if self.launching
                       else self.launch_error or "Google MRT2 stopped; browser sound remains available.",
        }

    def status(self):
        with self.lock:
            if self.launching:
                return self._inactive_status()
            if self.process is None or self.process.poll() is not None:
                return self._inactive_status()
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
            if set(data) != ACTIONS[action] and not (action == "start" and set(data) == {"prompts"}):
                raise ValueError("invalid AI action fields")
            if action == "configure-prompts" or (action == "start" and "prompts" in data):
                strings = data["prompts"]
                if (
                    not isinstance(strings, list)
                    or len(strings) != 4
                    or any(type(p) is not str or not p.strip() or len(p) > 500 for p in strings)
                ):
                    raise ValueError("provide four nonempty text prompts, each at most 500 characters")
            if action == "scene":
                if type(data["scene"]) is not str or data["scene"] not in ("pyramid", "fishes"):
                    raise ValueError("scene must be pyramid or fishes")
            if action == "lead-mix":
                if type(data["scene"]) is not str or data["scene"] not in ("pyramid", "fishes"):
                    raise ValueError("lead-mix scene must be pyramid or fishes")
            if action in ("mix", "volume", "reverb", "lead-mix"):
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
            if action == "start" and self.launching:
                return self._inactive_status()
            if action == "start":
                self.launch_error = ""
                self._start()
                if "prompts" in data:
                    response = self._request({"op": "configure-prompts", "prompts": data["prompts"]})
                    if response.get("error"):
                        raise RuntimeError(str(response["error"])[:180])
                return self._request({"op": "start"})
            elif self.process is None or self.process.poll() is not None:
                if action == "stop":
                    return self.status()
                raise RuntimeError("MRT2 not running: press ENABLE MAGENTA first")
            return self._request({"op": action, **data})

    def close(self):
        with self.lock:
            self.closing = True
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
