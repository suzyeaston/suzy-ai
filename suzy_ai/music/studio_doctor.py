"""Read-only preflight for a local Logic + MRT2 Small music session.

This tool never starts/stops processes, changes audio devices, or declares Logic
recording proved. Observations are not substitutes for an audible soundcheck.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess


def command(argv):
    """Bounded, read-only system query. Return None if unavailable."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=8,
                           check=False)
        return p.stdout if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def inspect(*, system=None, machine=None, run=command, audio_names=None,
            midi_names=None):
    """Return honest observations. Pass device lists for hardware-free tests."""
    system = platform.system() if system is None else system
    machine = platform.machine() if machine is None else machine
    checks = []

    def add(status, name, detail):
        checks.append({"status": status, "name": name, "detail": detail})

    supported = system == "Darwin" and machine in ("arm64", "aarch64")
    add("PASS" if supported else "FAIL", "Apple Silicon macOS",
        f"Detected {system}/{machine}; MRT2 requires Apple Silicon macOS")

    if audio_names is None:
        try:
            import sounddevice as sd
            audio_names = [d["name"] for d in sd.query_devices()]
        except (ImportError, OSError, ValueError, RuntimeError):
            audio_names = None
    if midi_names is None:
        try:
            import rtmidi
            m = rtmidi.MidiIn()
            midi_names = m.get_ports()
            del m
        except (ImportError, OSError, RuntimeError):
            midi_names = None

    def detect(label, names, term, guidance):
        if names is None:
            add("CHECK", label, guidance + " (enumeration unavailable)")
        elif any(term in name.casefold() for name in names):
            add("PASS", label, "Device name found; actual audio/MIDI path untested")
        else:
            add("WARN", label, guidance + " (not found in enumerated devices)")

    detect("Scarlett audio interface", audio_names, "scarlett",
           "Connect Scarlett and inspect macOS audio devices")
    detect("Keystation MIDI controller", midi_names, "keystation",
           "Connect Keystation and inspect CoreMIDI input ports")

    if supported:
        units = run(["pluginkit", "-mAv"])
        if units is None:
            add("CHECK", "MRT2 Audio Unit", "Could not query AUv3 registry")
        elif "mrt2" in units.casefold() or "magenta" in units.casefold():
            add("PASS", "MRT2 Audio Unit", "Possible Magenta AU registered; open it in Logic to verify")
        else:
            add("WARN", "MRT2 Audio Unit", "No Magenta/MRT2 entry in pluginkit output")
        processes = run(["pgrep", "-fl", "llama-server|llama.cpp"])
        if processes is None:
            add("CHECK", "Qwen resource contention", "Process query unavailable or no matching process; verify manually")
        elif processes.strip():
            add("WARN", "Qwen resource contention", "A matching process appears active; review manually before show")
    else:
        add("CHECK", "MRT2 Audio Unit", "Inspect on the performance Mac")
        add("CHECK", "Qwen resource contention", "Inspect on the performance Mac")

    for item in ("Logic project is 48 kHz", "AI produces audible sound in Logic",
                 "Logic AI-track mute silences output", "Vocal and MIDI take saved",
                 "AI audio bounced, saved, reopened", "Offline and endurance rehearsal"):
        add("CHECK", item, "Requires musician-observed test in Logic; this tool cannot verify it")
    return {"checks": checks, "ready": False,
            "summary": "PRECHECK ONLY: not a certification of stage readiness"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output preflight JSON")
    args = parser.parse_args(argv)
    result = inspect()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("SUZY//AI STUDIO PRECHECK")
        for item in result["checks"]:
            print(f"{item['status']:5}  {item['name']}: {item['detail']}")
        print("\n" + result["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
