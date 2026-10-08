from __future__ import annotations

import json
import socket
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, memory
from .chat import chat
from .inference import InferenceError, InferenceTimeout, InferenceUnavailable
from .events import timeline_event
from .registry import load_registry
from .store import append_event, read_events
from .world import list_entities, list_teachings, stats, teach


ROOT = Path(__file__).resolve().parents[1]
LOCAL_UI = ROOT / "site" / "local" / "index.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "SUZYAI/0.3"
    inference_slot = threading.BoundedSemaphore(1)

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(15)
        self._discard_input = False

    def finish(self) -> None:
        try:
            super().finish()
        finally:
            if self._discard_input:
                # Deliver the rejection before closing a socket with unread input.
                # A bounded drain avoids a TCP reset swallowing the response on
                # macOS, without accepting or allocating an oversized body.
                try:
                    self.connection.shutdown(socket.SHUT_WR)
                    deadline = time.monotonic() + 0.1
                    remaining = 262_144
                    while remaining:
                        time_left = deadline - time.monotonic()
                        if time_left <= 0:
                            break
                        self.connection.settimeout(time_left)
                        chunk = self.connection.recv(min(remaining, 16_384))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                except OSError:
                    pass

    def _trusted_request(self) -> bool:
        # Reject DNS rebinding and cross-origin browser access on every route.
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        if port == 80:
            hosts.update({"127.0.0.1", "localhost", "[::1]"})
        host = self.headers.get("Host", "")
        origins = self.headers.get_all("Origin", [])
        if (len(self.headers.get_all("Host", [])) != 1 or host not in hosts
                or len(origins) > 1
                or (origins and origins[0] != f"http://{host}")
                or self.headers.get("Sec-Fetch-Site") == "cross-site"):
            self._discard_input = True
            self._json({"error": "only same-origin local requests are allowed"}, 403)
            return False
        return True

    def _dispatch(self, callback) -> None:
        if not self._trusted_request():
            return
        try:
            callback()
        except InferenceTimeout as exc:
            self._json({"error": str(exc)}, 504)
        except InferenceUnavailable as exc:
            self._json({"error": str(exc)}, 503)
        except InferenceError as exc:
            self._json({"error": str(exc)}, 502)
        except (TypeError, ValueError, UnicodeError, RecursionError):
            self._json({"error": "invalid request"}, 400)
        except (sqlite3.Error, OSError):
            self._json({"error": "local storage or connection unavailable"}, 503)

    def _headers(
        self,
        status: int = 200,
        content_type: str = "application/json; charset=utf-8",
        content_length: int = 0,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

    def _json(self, payload: object, status: int = 200) -> None:
        body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self._headers(status, content_length=len(body))
        self.wfile.write(body)

    def _html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self._headers(status, "text/html; charset=utf-8", len(encoded))
        self.wfile.write(encoded)

    def _body(self) -> dict:
        self._discard_input = True
        if (self.headers.get_content_type() != "application/json"
                or self.headers.get("Transfer-Encoding")
                or len(self.headers.get_all("Content-Length", [])) != 1):
            raise ValueError("JSON with a single Content-Length is required")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 131_072:
            raise ValueError("invalid request size")
        raw = self.rfile.read(length)
        self._discard_input = False
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def do_OPTIONS(self) -> None:
        if self._trusted_request():
            self._headers(204)

    def do_GET(self) -> None:
        self._dispatch(self._get)

    def _get(self) -> None:
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
                    "version": __version__,
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
        self._dispatch(self._post)

    def _post(self) -> None:
        parsed = urlparse(self.path)

        try:
            payload = self._body()
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, 400)
            return

        if parsed.path == "/v1/chat":
            if not self.inference_slot.acquire(blocking=False):
                self._json({"error": "local inference is busy; retry later"}, 429)
                return
            try:
                self._json(chat(payload))
            finally:
                self.inference_slot.release()
            return

        if parsed.path == "/v1/memory":
            if set(payload) != {"title", "text", "source", "approved"}:
                raise ValueError("title, text, source and approved are required")
            self._json(memory.add(**payload), 201)
            return

        if parsed.path == "/v1/memory/search":
            if set(payload) - {"query", "limit"} or "query" not in payload:
                raise ValueError("query and optional limit are accepted")
            self._json({"sources": memory.search(**payload)})
            return

        if parsed.path == "/v1/memory/delete":
            if set(payload) != {"id"}:
                raise ValueError("id is required")
            deleted = memory.delete(payload["id"])
            self._json({"deleted": deleted}, 200 if deleted else 404)
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

            if not isinstance(position, dict):
                raise ValueError("position must be an object")

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
        # Request URLs, bodies, and model responses can contain private data.
        pass


def serve(host: str = "127.0.0.1", port: int = 7331) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("SUZY//AI only binds to loopback")
    if host == "::1":
        class IPv6Server(ThreadingHTTPServer):
            address_family = socket.AF_INET6
        server = IPv6Server((host, port), Handler)
    else:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"SUZY//AI listening on http://{host}:{port}")
    print("Local loopback only. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSUZY//AI stopped.")
    finally:
        server.server_close()
