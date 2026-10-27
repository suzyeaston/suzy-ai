"""Independent localhost MIDI-only stage UI for Magenta Jam / Logic AU.

Run: python -m suzy_ai.music.magenta_stage
No sounddevice, Qwen, audio capture, or model server is started.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
from pathlib import Path
import platform
import secrets

from .magenta_midi import MagentaMidiBridge
from .toaster_performance import ToasterPerformance
from .audio_routing import inspect_audio_routing
from .magenta_native_host import NativeMagentaHost

PAGE = Path(__file__).with_name("magenta_stage.html")
TOASTER_PAGE = Path(__file__).with_name("toaster_stage.html")
LIVE_PAGE = Path(__file__).with_name("toaster_live.html")
PLAY_PAGE = Path(__file__).with_name("toaster_play.html")
LOOP_RACK_SCRIPT = Path(__file__).with_name("toaster_loop_rack.js")


class MagentaStageHandler(BaseHTTPRequestHandler):
    bridge: MagentaMidiBridge
    token: str
    performance: ToasterPerformance | None = None
    native_host: NativeMagentaHost | None = None

    def log_message(self, fmt, *args):
        pass

    def reply(self, status, body, content_type="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        for k, v in [
            ("Content-Type", content_type),
            ("Content-Length", str(len(raw))),
            ("Cache-Control", "no-store"),
            ("X-Frame-Options", "DENY"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            ("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; "
             "script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'"),
        ]:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/":
            page = PAGE.read_text(encoding="utf8").replace("__MAGENTA_TOKEN__", self.token)
            return self.reply(200, page.encode("utf8"), "text/html; charset=utf-8")
        if self.path == "/toaster":
            page = TOASTER_PAGE.read_text(encoding="utf8").replace("__MAGENTA_TOKEN__", self.token)
            return self.reply(200, page.encode("utf8"), "text/html; charset=utf-8")
        if self.path == "/toaster/live":
            page = PLAY_PAGE.read_text(encoding="utf8").replace("__MAGENTA_TOKEN__", self.token)
            return self.reply(200, page.encode("utf8"), "text/html; charset=utf-8")
        if self.path == "/toaster/studio":
            page = LIVE_PAGE.read_text(encoding="utf8").replace("__MAGENTA_TOKEN__", self.token)
            return self.reply(200, page.encode("utf8"), "text/html; charset=utf-8")
        if self.path == "/toaster/loop-rack.js":
            return self.reply(200, LOOP_RACK_SCRIPT.read_bytes(), "text/javascript; charset=utf-8")
        if self.path == "/api/ai/status":
            return self.reply(200, self.native_host.status() if self.native_host else {"phase":"not-configured"})
        if self.path == "/api/perform/status":
            return self.reply(200, self.performance.status()) if self.performance else self.reply(503, {"error":"performance unavailable"})
        if self.path == "/api/status":
            return self.reply(200, self.bridge.status())
        if self.path == "/api/inputs":
            return self.reply(200, {"inputs": self.bridge.inputs()})
        if self.path == "/api/audio-routing":
            return self.reply(200, inspect_audio_routing())
        return self.reply(404, {"error": "unknown route"})

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and origin != f"http://127.0.0.1:{self.server.server_port}":
            return self.reply(403, {"error": "untrusted browser origin"})
        if not hmac.compare_digest(self.headers.get("X-Suzy-Token", ""), self.token):
            return self.reply(403, {"error": "missing local control token"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, {"error": "JSON body required"})
        length = self.headers.get("Content-Length", "")
        if not length.isdecimal() or not 0 <= int(length) <= 2048:
            self.close_connection = True
            return self.reply(413, {"error": "invalid request length"})
        try:
            data = json.loads(self.rfile.read(int(length)))
            if not isinstance(data, dict):
                raise ValueError("JSON object expected")
            if self.path.startswith("/api/ai/"):
                if self.native_host is None:
                    return self.reply(503, {"error": "native Magenta bridge not configured"})
                result = self.native_host.command(self.path.removeprefix("/api/ai/"), data)
            elif self.path in ("/api/collider/connect", "/api/collider/disconnect"):
                if data:
                    raise ValueError("Collider MIDI command takes no arguments")
                # Release TOASTER chord/groove before changing destination.
                if self.performance is not None:
                    self.performance.stop()
                if self.path == "/api/collider/connect":
                    self.bridge.connect_collider()
                else:
                    self.bridge.disconnect_collider()
                result = self.performance.status() if self.performance else self.bridge.status()
            elif self.path.startswith("/api/perform/"):
                perf = self.performance
                if perf is None:
                    return self.reply(503, {"error": "performance unavailable"})
                if self.path == "/api/perform/scene":
                    if set(data) != {"scene"}: raise ValueError("scene required")
                    result = perf.scene_change(data["scene"])
                elif self.path == "/api/perform/chord":
                    if set(data) != {"index"}: raise ValueError("index required")
                    result = perf.chord(data["index"])
                elif self.path == "/api/perform/release-chord":
                    if data: raise ValueError("release-chord takes no arguments")
                    result = perf.release_chord()
                elif self.path == "/api/perform/settings":
                    if set(data) != {"bpm","rhythm","intensity"}: raise ValueError("bpm, rhythm, intensity required")
                    result = perf.settings(**data)
                elif self.path == "/api/perform/start":
                    if data: raise ValueError("start takes no arguments")
                    result = perf.start()
                elif self.path == "/api/perform/stop":
                    if data: raise ValueError("stop takes no arguments")
                    result = perf.stop()
                else:
                    return self.reply(404, {"error": "unknown action"})
            elif self.path == "/api/select":
                if set(data) != {"input"}:
                    raise ValueError("input required")
                result = self.bridge.connect(data["input"])
            elif self.path == "/api/disconnect":
                if data:
                    raise ValueError("disconnect requires no arguments")
                result = self.bridge.disconnect()
            elif self.path == "/api/mode":
                if set(data) != {"mode"}:
                    raise ValueError("mode required")
                result = self.bridge.change_mode(data["mode"])
            elif self.path == "/api/gate":
                if set(data) != {"open"}:
                    raise ValueError("open flag required")
                if data["open"] is False and self.performance is not None:
                    self.performance.stop()
                result = self.bridge.set_gate(data["open"])
            elif self.path == "/api/release":
                if data:
                    raise ValueError("release requires no arguments")
                if self.performance is not None:
                    self.performance.stop()
                result = self.bridge.release()
            elif self.path == "/api/test":
                if data:
                    raise ValueError("test requires no arguments")
                result = self.bridge.test_chord()
            else:
                return self.reply(404, {"error": "unknown action"})
        except RuntimeError as exc:
            return self.reply(503, {"error": str(exc)[:180]})
        except (ValueError, TypeError, KeyError) as exc:
            return self.reply(400, {"error": str(exc)[:180]})
        except Exception:
            # Do not leak OS/device internals to the browser.
            return self.reply(503, {"error": "MIDI device operation failed; use RELEASE or stop this server"})
        return self.reply(200, result)


def main(argv=None):
    parser = argparse.ArgumentParser(description="SUZY//AI virtual CoreMIDI performance steering")
    parser.add_argument("--port", type=int, default=7345)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("use a high localhost port")
    if platform.system() != "Darwin":
        parser.error("the stage MIDI bridge requires macOS CoreMIDI")
    try:
        import rtmidi
    except ImportError:
        parser.error('Install python-rtmidi: .venv-mac/bin/python -m pip install -e ".[live-midi]"')
    bridge = MagentaMidiBridge(rtmidi)
    class Handler(MagentaStageHandler):
        pass
    Handler.bridge = bridge
    Handler.performance = ToasterPerformance(bridge)
    Handler.native_host = NativeMagentaHost()
    Handler.token = secrets.token_urlsafe(32)
    try:
        with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
            server.daemon_threads = True
            print(f"SUZY//AI MAGENTA MIDI STAGE http://127.0.0.1:{args.port}/", flush=True)
            print(f"SUZY//TOAST SIMPLE PLAY http://127.0.0.1:{args.port}/toaster/live", flush=True)
            print(f"SUZY//TOAST ADVANCED STUDIO http://127.0.0.1:{args.port}/toaster/studio", flush=True)
            print(f"SUZY//TOAST prototype http://127.0.0.1:{args.port}/toaster", flush=True)
            print("Choose 'SUZY AI MIDI' as Jam's MIDI INPUT. Deselect physical Keystation in Jam.", flush=True)
            print("This app only steers MIDI. For real audio mute, use Magenta/Logic controls.", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        Handler.performance.close()
        Handler.native_host.close()
        bridge.close()


if __name__ == "__main__":
    main()
