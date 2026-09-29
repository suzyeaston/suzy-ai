from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .events import timeline_event
from .registry import load_registry
from .store import append_event, read_events


class Handler(BaseHTTPRequestHandler):
    server_version = "SUZYAI/0.1"

    def _headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # v0.1 binds to loopback only. Wildcard CORS lets local browser apps
        # such as Vite dev servers talk to the core without browser hacks.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _json(self, payload: object, status: int = 200) -> None:
        self._headers(status)
        self.wfile.write(
            (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )

    def do_OPTIONS(self) -> None:
        self._headers(204)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._json(
                {
                    "ok": True,
                    "name": "SUZY//AI",
                    "version": "0.1.0",
                    "mode": "local-first",
                }
            )
            return

        if parsed.path == "/v1/apps":
            self._json(load_registry())
            return

        if parsed.path == "/v1/timeline":
            query = parse_qs(parsed.query)
            stream = (query.get("stream") or [None])[0]
            self._json({"events": read_events(stream)})
            return

        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/v1/events":
            self._json({"error": "not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, 400)
            return

        required = ("stream", "kind", "source", "payload")
        missing = [key for key in required if key not in payload]
        if missing:
            self._json({"error": f"missing fields: {', '.join(missing)}"}, 400)
            return

        position = payload.get("position") or {
            "unit": "iso8601",
            "value": payload.get("at") or "",
        }

        event = timeline_event(
            stream=str(payload["stream"]),
            kind=str(payload["kind"]),
            source=str(payload["source"]),
            unit=str(position.get("unit", "iso8601")),
            value=position.get("value", ""),
            payload=dict(payload["payload"]),
            confidence=payload.get("confidence"),
        )
        append_event(event)
        self._json(event, 201)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[suzy-ai] {self.address_string()} - {format % args}")


def serve(host: str = "127.0.0.1", port: int = 7331) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"SUZY//AI listening on http://{host}:{port}")
    print("Local loopback only. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSUZY//AI stopped.")
    finally:
        server.server_close()
