"""Read-only CoreAudio/PortAudio discovery for performer setup.

A MIDI-only SUZY bridge cannot choose Magenta Jam's audio output or Logic's
input/output devices. Default PortAudio indices are not a Logic device setting.
"""
from __future__ import annotations


def inspect_audio_routing(sounddevice=None):
    """No devices are opened or changed. Optional dependency is lazily imported."""
    try:
        if sounddevice is None:
            import sounddevice as sounddevice
        raw = sounddevice.query_devices()
        selected = sounddevice.default.device
        if not isinstance(selected, (list, tuple)) or len(selected) != 2:
            selected = (-1, -1)
        defaults = tuple(int(i) if type(i) is int and i >= 0 else -1 for i in selected)
        devices = []
        for index, d in enumerate(raw):
            in_channels = max(0, int(d.get("max_input_channels", 0)))
            out_channels = max(0, int(d.get("max_output_channels", 0)))
            if not (in_channels or out_channels):
                continue
            name = str(d.get("name", "Unnamed device"))[:100]
            devices.append({
                "id": index,
                "name": name,
                "input_channels": in_channels,
                "output_channels": out_channels,
                "system_default_input": index == defaults[0],
                "system_default_output": index == defaults[1],
                "scarlett_candidate": "scarlett" in name.casefold() or "focusrite" in name.casefold(),
            })
        return {
            "available": True,
            "devices": devices,
            "message": "Device discovery only. Select audio inputs/outputs in Logic Pro or the standalone app.",
            "logic_audio_device_observed": False,
            "magenta_audio_observed": False,
            "can_change_host_audio_output": False,
        }
    except (ImportError, OSError, RuntimeError, ValueError, TypeError, OverflowError):
        return {
            "available": False,
            "devices": [],
            "message": "Could not enumerate CoreAudio devices. Install .[live-midi] or inspect Audio MIDI Setup.",
            "logic_audio_device_observed": False,
            "magenta_audio_observed": False,
            "can_change_host_audio_output": False,
        }
