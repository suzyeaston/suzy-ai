"""Experimental loopback-only live performance panel: Scarlett -> local Qwen -> headphones.

Phrase-by-phrase, not beat-clock synchronized; NEVER captures Logic's internal
buses, runs AI in an audio callback, writes microphone recordings, or changes
Logic playback. Audio work is in-memory and opt-in; Stop invalidates late AI.
"""
from __future__ import annotations
from array import array
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import hmac
import json
import math
from pathlib import Path
import secrets
import sys
import threading
import time

from .counterline import render_counterline
from .phrase import extract_phrase
from .qwen_composer import CompositionError, LocalQwenComposer

RATE = 48000
BLOCK = 512
MAX_FRAMES = RATE * 8
PAGE = Path(__file__).with_name("stage_panel.html")


def _mic_mono(data: bytes, channels: int, channel: int) -> bytes:
    if channels not in (1, 2) or not 0 <= channel < channels:
        raise ValueError("invalid physical mic input channel")
    samples = array("h")
    samples.frombytes(data)
    if sys.byteorder != "little":
        samples.byteswap()
    if channels == 2:
        samples = samples[channel::2]
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def _peak(pcm: bytes) -> float:
    samples = array("h")
    samples.frombytes(pcm)
    return round(max((abs(x) for x in samples), default=0) / 32768, 4)


def _validate_controls(data):
    if not isinstance(data, dict) or set(data) != {
            "bpm", "beats", "instruction", "chord", "research"}:
        raise ValueError("invalid musical controls")
    bpm, beats = data["bpm"], data["beats"]
    if (type(bpm) not in (int, float) or not math.isfinite(bpm)
            or not 40 <= bpm <= 240 or type(beats) is not int
            or beats not in (4, 8, 12, 16)):
        raise ValueError("use 40-240 BPM and 4, 8, 12, or 16 beats")
    seconds = beats * 60 / bpm
    if not 1.5 <= seconds <= 8:
        raise ValueError("choose a 1.5-8 second capture")
    instruction, chord, research = (data[k] for k in ("instruction", "chord", "research"))
    if not isinstance(instruction, str) or not 1 <= len(instruction.strip()) <= 250:
        raise ValueError("enter a brief performance instruction")
    if chord is not None and (not isinstance(chord, str) or len(chord) > 20 or
                              any(c not in "ABCDEFGabcdefg#b0123456789mMajinsud/()+- " for c in chord)):
        raise ValueError("invalid optional supplied chord")
    if type(research) is not bool:
        raise ValueError("research must be on or off")
    return dict(bpm=bpm, beats=beats, seconds=seconds,
                instruction=instruction.strip(), chord=chord or None, research=research)


class StageEngine:
    """Bounded manual capture; callback only copies PCM, never calls Qwen."""
    def __init__(self, sd, composer=None):
        self.sd = sd
        self.composer = composer if composer is not None else LocalQwenComposer()
        self.lock = threading.RLock()
        self.stream = None
        self.input_id = self.output_id = None
        self.channels = 0
        self.channel = 0
        self.state = "disconnected"
        self.error = None
        self.generation = 0
        self.input_buffer = bytearray(MAX_FRAMES * 4)
        self.target_bytes = self.bytes_written = 0
        self.recording = self.playing = False
        self.playback = b""
        self.play_offset = 0
        self.repeats = 1
        self.after_play = "ready"
        self.plan = None
        self.peak = None
        self.elapsed = None
        self.controls = None
        self.shutdown = threading.Event()
        self.monitor = threading.Thread(target=self._monitor, daemon=True)
        self.monitor.start()

    def devices(self):
        inputs, outputs = [], []
        for i, v in enumerate(self.sd.query_devices()):
            inp, out = int(v["max_input_channels"]), int(v["max_output_channels"])
            if inp > 0:
                inputs.append({"id": i, "name": str(v["name"])[:100], "channels": inp})
            if out >= 2:
                outputs.append({"id": i, "name": str(v["name"])[:100], "channels": out})
        return {"inputs": inputs, "outputs": outputs}

    def status(self):
        with self.lock:
            return {
                "state": self.state, "error": self.error,
                "connected": self.stream is not None,
                "input_id": self.input_id, "output_id": self.output_id,
                "mic_channel": self.channel + 1, "input_channels": self.channels,
                "capture_seconds": round(self.target_bytes / (RATE*self.channels*2), 2)
                    if self.target_bytes and self.channels else 0,
                "progress": round(min(1, self.bytes_written / self.target_bytes), 3)
                    if self.target_bytes else 0,
                "peak": self.peak, "elapsed_seconds": self.elapsed,
                "model": self.plan.get("model") if self.plan else None,
                "notes": self.plan.get("events", []) if self.plan else [],
                "references_offered": self.plan.get("references_offered", []) if self.plan else [],
                "reference_used": self.plan.get("reference_used") if self.plan else None,
                "routing_note": "Mic only. Logic backing is NOT routed into Qwen.",
            }

    def _close_stream(self):
        self.recording = self.playing = False
        if self.stream is not None:
            try:
                self.stream.stop()
            finally:
                self.stream.close()
            self.stream = None

    def connect(self, data):
        if not isinstance(data, dict) or set(data) != {"input_id", "output_id", "mic_channel"}:
            raise ValueError("select physical mic, output and input channel")
        inp, out, ch = (data[k] for k in ("input_id", "output_id", "mic_channel"))
        devices = self.devices()
        inputs = {v["id"]: v for v in devices["inputs"]}
        outputs = {v["id"]: v for v in devices["outputs"]}
        if (type(inp) is not int or type(out) is not int or type(ch) is not int
                or inp not in inputs or out not in outputs
                or ch not in (1,2) or ch > min(2,inputs[inp]["channels"])):
            raise ValueError("invalid device or physical microphone channel")
        with self.lock:
            if self.state in ("capturing", "captured", "processing", "playing"):
                raise ValueError("stop AI before changing devices")
            self._close_stream()
            self.generation += 1
            self.channels = min(2, inputs[inp]["channels"])
            self.channel = ch - 1
            stream = None
            try:
                stream = self.sd.RawStream(
                    device=(inp, out), samplerate=RATE, blocksize=BLOCK,
                    channels=(self.channels, 2), dtype="int16", callback=self._callback)
                stream.start()
            except Exception:
                if stream is not None:
                    try: stream.close()
                    except Exception: pass
                self.state = "disconnected"
                raise ValueError("Cannot open 48kHz audio device; check Mac microphone permission, device ownership and output") from None
            self.stream = stream
            self.input_id, self.output_id = inp, out
            self.state, self.error = "idle", None
            self.plan = None
            return self.status()

    def _callback(self, indata, outdata, frames, time_info, status):
        """Single callback owns hardware; no inference, file I/O or model calls."""
        outdata[:] = b"\0" * len(outdata)
        if self.recording:
            count = min(self.target_bytes-self.bytes_written,
                        frames*self.channels*2)
            if count:
                self.input_buffer[self.bytes_written:self.bytes_written+count] = indata[:count]
                self.bytes_written += count
            if self.bytes_written >= self.target_bytes:
                self.recording = False
                self.state = "captured"
        if self.playing and self.playback:
            remaining = len(self.playback)*self.repeats-self.play_offset
            at = 0
            while at < len(outdata) and remaining > 0:
                start = self.play_offset % len(self.playback)
                n = min(len(self.playback)-start,len(outdata)-at,remaining)
                outdata[at:at+n] = self.playback[start:start+n]
                self.play_offset += n
                at += n
                remaining -= n
            if remaining == 0:
                self.playing = False
                self.state = self.after_play

    def arm(self, data):
        controls = _validate_controls(data)
        with self.lock:
            if self.stream is None or self.state not in ("idle","ready","failed"):
                raise ValueError("connect a device, then finish or stop the previous phrase")
            self.generation += 1
            self.controls = controls
            self.plan = None
            self.error = self.peak = self.elapsed = None
            self.bytes_written = 0
            self.target_bytes = round(controls["seconds"]*RATE)*self.channels*2
            if self.target_bytes > len(self.input_buffer):
                raise ValueError("audio capture is too long")
            self.playing = False
            self.recording = True
            self.state = "capturing"
            return self.status()

    def _monitor(self):
        while not self.shutdown.wait(.03):
            with self.lock:
                if self.state != "captured":
                    continue
                self.state = "processing"
                generation = self.generation
                pcm = bytes(self.input_buffer[:self.bytes_written])
                controls = dict(self.controls)
                channels, channel = self.channels, self.channel
            threading.Thread(target=self._compose,
                             args=(generation,pcm,controls,channels,channel),
                             daemon=True).start()

    def _compose(self, generation, captured, controls, channels, channel):
        started = time.monotonic()
        try:
            mono = _mic_mono(captured,channels,channel)
            peak = _peak(mono)
            if peak < .006:
                raise CompositionError("Mic channel is too quiet; check Scarlett gain or channel selection")
            phrase = extract_phrase(mono,rate=RATE,channels=1,bpm=controls["bpm"])
            plan = self.composer(
                phrase,instruction=controls["instruction"],
                use_deep_research=controls["research"],
                accompaniment={"half_beat_energy":[],"chord":controls["chord"]})
            pcm = render_counterline(plan,rate=RATE)
            if not pcm:
                raise CompositionError("Qwen did not compose audible notes")
            with self.lock:
                if generation != self.generation or self.state != "processing":
                    return
                self.plan = plan
                self.playback = pcm
                self.peak = peak
                self.elapsed = round(time.monotonic()-started,2)
                self.state = "ready"
        except Exception as exc:
            message = str(exc) if isinstance(exc,CompositionError) else "Audio/model operation failed"
            with self.lock:
                if generation == self.generation and self.state == "processing":
                    self.state = "failed"
                    self.error = message[:180]
                    self.elapsed = round(time.monotonic()-started,2)

    def audition(self, repeats):
        if type(repeats) is not int or not 1 <= repeats <= 4:
            raise ValueError("repeat count must be 1-4")
        with self.lock:
            if self.state != "ready" or not self.playback:
                raise ValueError("capture a vocal phrase and wait for Qwen first")
            self.repeats, self.play_offset = repeats, 0
            self.after_play = "ready"
            self.state = "playing"
            self.playing = True
            return self.status()

    def test(self):
        with self.lock:
            if self.stream is None or self.state not in ("idle","failed"):
                raise ValueError("test output before capture, or stop the current AI response first")
            from .live_probe import diagnostic_tone
            self.playback = diagnostic_tone(duration=.6,amplitude=.035)
            self.repeats,self.play_offset = 1,0
            self.after_play = self.state
            self.state = "playing"
            self.playing = True
            return self.status()

    def stop(self):
        with self.lock:
            self.generation += 1
            self.recording = self.playing = False
            self.playback = b""
            self.plan = None
            self.error = None
            self.state = "idle" if self.stream is not None else "disconnected"
            return self.status()

    def close(self):
        self.shutdown.set()
        with self.lock:
            self.generation += 1
            self._close_stream()
            self.state = "disconnected"


class PanelHandler(BaseHTTPRequestHandler):
    engine: StageEngine
    token: str

    def log_message(self, fmt, *args):
        pass

    def _send(self, status, data, ctype="application/json; charset=utf-8"):
        raw = data if isinstance(data,bytes) else json.dumps(data).encode()
        self.send_response(status)
        for key,value in (
            ("Content-Type",ctype),("Content-Length",str(len(raw))),
            ("Cache-Control","no-store"),("X-Frame-Options","DENY"),
            ("X-Content-Type-Options","nosniff"),("Referrer-Policy","no-referrer"),
            ("Content-Security-Policy",
             "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'"),
        ):
            self.send_header(key,value)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/":
            page = PAGE.read_text(encoding="utf8").replace("__SUZY_PANEL_TOKEN__",self.token)
            return self._send(200,page.encode(),"text/html; charset=utf-8")
        if self.path == "/api/devices":
            return self._send(200,self.engine.devices())
        if self.path == "/api/status":
            return self._send(200,self.engine.status())
        return self._send(404,{"error":"unknown route"})

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and origin != f"http://127.0.0.1:{self.server.server_port}":
            return self._send(403,{"error":"untrusted browser origin"})
        if not hmac.compare_digest(self.headers.get("X-Suzy-Panel-Token",""),self.token):
            return self._send(403,{"error":"local panel token required"})
        if self.headers.get("Content-Type","").split(";")[0] != "application/json":
            return self._send(415,{"error":"JSON body required"})
        length = self.headers.get("Content-Length","")
        if not length.isdecimal() or not 0 <= int(length) <= 2048:
            self.close_connection = True
            return self._send(413,{"error":"request too large"})
        try:
            data = json.loads(self.rfile.read(int(length)))
            if self.path == "/api/connect":
                result = self.engine.connect(data)
            elif self.path == "/api/arm":
                result = self.engine.arm(data)
            elif self.path == "/api/audition":
                if not isinstance(data,dict) or set(data) != {"repeats"}:
                    raise ValueError("invalid audition request")
                result = self.engine.audition(data["repeats"])
            elif self.path == "/api/test":
                if data != {}: raise ValueError("test tone needs no arguments")
                result = self.engine.test()
            elif self.path == "/api/stop":
                if data != {}: raise ValueError("stop AI needs no arguments")
                result = self.engine.stop()
            else:
                return self._send(404,{"error":"unknown action"})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            return self._send(400,{"error":str(exc)[:180]})
        return self._send(200,result)


def main():
    parser = argparse.ArgumentParser(description="SUZY//AI local Focusrite performance controls")
    parser.add_argument("--port",type=int,default=7344)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("use a high localhost port")
    try:
        import sounddevice
    except ImportError:
        parser.error('Install optional audio dependency: .venv-mac/bin/python -m pip install -e ".[live]"')
    engine = StageEngine(sounddevice)
    class LocalHandler(PanelHandler): pass
    LocalHandler.engine = engine
    LocalHandler.token = secrets.token_urlsafe(32)
    try:
        with ThreadingHTTPServer(("127.0.0.1",args.port),LocalHandler) as server:
            server.daemon_threads = True
            print(f"SUZY//AI LIVE PANEL http://127.0.0.1:{args.port}/",flush=True)
            print("HEADPHONES + low volume. Focusrite mic only, NOT Logic audio bus.",flush=True)
            print("Stop AI in panel; Ctrl-C closes the audio device.",flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.close()


if __name__ == "__main__":
    main()
