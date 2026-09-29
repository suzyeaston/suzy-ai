from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .events import timeline_event
from .registry import load_registry
from .store import append_event, read_events
from .world import list_entities, list_teachings, stats, teach


ROOT = Path(__file__).resolve().parents[1]
LOCAL_UI = ROOT / "site" / "local" / "index.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "SUZYAI/0.2"

    def _headers(
        self,
        status: int = 200,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _json(self, payload: object, status: int = 200) -> None:
        self._headers(status)
        self.wfile.write(
            (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )

    def _html(self, body: str, status: int = 200) -> None:
        self._headers(status, "text/html; charset=utf-8")
        self.wfile.write(body.encode("utf-8"))

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 1_000_000:
            raise ValueError("invalid request size")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def do_OPTIONS(self) -> None:
        self._headers(204)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/":
            if LOCAL_UI.exists():
                self._html(LOCAL_UI.read_text(encoding="utf-8"))
            else:
                self._html("<h1>SUZY//AI</h1><p>Local UI file is missing.</p>", 500)
            return

        if parsed.path == "/health":
            self._json(
                {
                    "ok": True,
                    "name": "SUZY//AI",
                    "version": "0.2.0",
                    "mode": "local-first",
                    "world_model": True,
                }
            )
            return

        if parsed.path == "/v1/apps":
            self._json(load_registry())
            return

        if parsed.path == "/v1/timeline":
            stream = (query.get("stream") or [None])[0]
            self._json({"events": read_events(stream)})
            return

        if parsed.path == "/v1/world/stats":
            self._json(stats())
            return

        if parsed.path == "/v1/world/entities":
            kind = (query.get("kind") or [None])[0]
            limit = int((query.get("limit") or ["100"])[0])
            self._json({"entities": list_entities(kind, limit)})
            return

        if parsed.path == "/v1/world/teachings":
            entity_id = (query.get("entity_id") or [None])[0]
            domain = (query.get("domain") or [None])[0]
            teaching_kind = (query.get("teaching_kind") or [None])[0]
            limit = int((query.get("limit") or ["100"])[0])
            self._json(
                {
                    "teachings": list_teachings(
                        entity_id=entity_id,
                        domain=domain,
                        teaching_kind=teaching_kind,
                        limit=limit,
                    )
                }
            )
            return

        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        try:
            payload = self._body()
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, 400)
            return

        if parsed.path == "/v1/events":
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
            return

        try:
            if parsed.path == "/v1/teach":
                required = (
                    "entity_kind",
                    "canonical",
                    "name",
                    "domain",
                    "teaching_kind",
                    "payload",
                )
                missing = [key for key in required if key not in payload]
                if missing:
                    raise ValueError(f"missing fields: {', '.join(missing)}")

                result = teach(
                    entity_kind=str(payload["entity_kind"]),
                    canonical=str(payload["canonical"]),
                    name=str(payload["name"]),
                    domain=str(payload["domain"]),
                    teaching_kind=str(payload["teaching_kind"]),
                    payload=dict(payload["payload"]),
                    source=str(payload.get("source") or "human"),
                    metadata=dict(payload.get("metadata") or {}),
                )
                self._json(result, 200 if result["duplicate"] else 201)
                return

            if parsed.path == "/v1/teach/album":
                artist = str(payload.get("artist") or "").strip()
                album = str(payload.get("album") or "").strip()
                if not artist or not album:
                    raise ValueError("artist and album are required")

                teaching = {
                    key: value
                    for key, value in payload.items()
                    if key not in {"artist", "album", "source"}
                    and value not in ("", None, [], {})
                }

                result = teach(
                    entity_kind="album",
                    canonical=f"{artist}::{album}",
                    name=f"{artist} — {album}",
                    domain="music",
                    teaching_kind="album_review",
                    payload=teaching or {"note": "album noted"},
                    source=str(payload.get("source") or "human"),
                    metadata={
                        "artist": artist,
                        "album": album,
                        "year": payload.get("year"),
                    },
                )
                self._json(result, 200 if result["duplicate"] else 201)
                return

            if parsed.path == "/v1/teach/idiom":
                phrase = str(payload.get("phrase") or "").strip()
                if not phrase:
                    raise ValueError("phrase is required")

                teaching = {
                    key: value
                    for key, value in payload.items()
                    if key not in {"phrase", "source"}
                    and value not in ("", None, [], {})
                }

                result = teach(
                    entity_kind="idiom",
                    canonical=phrase,
                    name=phrase,
                    domain="language",
                    teaching_kind="idiom",
                    payload=teaching or {"meaning": "not supplied yet"},
                    source=str(payload.get("source") or "human"),
                    metadata={"phrase": phrase},
                )
                self._json(result, 200 if result["duplicate"] else 201)
                return

            if parsed.path == "/v1/teach/music":
                idea = str(
                    payload.get("idea")
                    or payload.get("chord")
                    or payload.get("title")
                    or ""
                ).strip()
                if not idea:
                    raise ValueError("idea/chord/title is required")

                voicing = str(payload.get("voicing") or "").strip()
                canonical = f"{idea}::{voicing}" if voicing else idea

                teaching = {
                    key: value
                    for key, value in payload.items()
                    if key not in {"idea", "chord", "title", "source"}
                    and value not in ("", None, [], {})
                }

                result = teach(
                    entity_kind="musical_idea",
                    canonical=canonical,
                    name=idea,
                    domain="music",
                    teaching_kind="musical_idea",
                    payload=teaching or {"note": "musical idea captured"},
                    source=str(payload.get("source") or "human"),
                    metadata={
                        "idea": idea,
                        "voicing": voicing or None,
                        "instrument": payload.get("instrument"),
                    },
                )
                self._json(result, 200 if result["duplicate"] else 201)
                return

            if parsed.path == "/v1/teach/world-note":
                domain = str(payload.get("domain") or "world").strip()
                subject = str(payload.get("subject") or "").strip()
                note = str(payload.get("note") or "").strip()
                if not subject or not note:
                    raise ValueError("subject and note are required")

                result = teach(
                    entity_kind=str(payload.get("entity_kind") or "subject"),
                    canonical=subject,
                    name=subject,
                    domain=domain,
                    teaching_kind=str(payload.get("teaching_kind") or "world_note"),
                    payload={
                        "note": note,
                        "connections": payload.get("connections") or [],
                        "changed_from": payload.get("changed_from"),
                    },
                    source=str(payload.get("source") or "human"),
                    metadata={"domain": domain},
                )
                self._json(result, 200 if result["duplicate"] else 201)
                return

        except (TypeError, ValueError) as exc:
            self._json({"error": str(exc)}, 400)
            return

        self._json({"error": "not found"}, 404)

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
