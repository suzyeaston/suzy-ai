from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

from .events import timeline_event
from .paths import ensure_home
from .store import append_event


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def world_db_path() -> Path:
    return ensure_home() / "world" / "world.sqlite3"


def canonicalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\s:+#()/.'’&-]", "", value, flags=re.UNICODE)
    return value


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def connect() -> sqlite3.Connection:
    path = world_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    init_schema(db)
    return db


def init_schema(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            canonical_key TEXT NOT NULL,
            name TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(kind, canonical_key)
        );

        CREATE TABLE IF NOT EXISTS teachings (
            id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            domain TEXT NOT NULL,
            teaching_kind TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            fingerprint TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_entities_kind
        ON entities(kind);

        CREATE INDEX IF NOT EXISTS idx_teachings_entity
        ON teachings(entity_id);

        CREATE INDEX IF NOT EXISTS idx_teachings_domain
        ON teachings(domain);

        CREATE INDEX IF NOT EXISTS idx_teachings_created
        ON teachings(created_at DESC);
        """
    )
    db.commit()


def _entity_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "kind": row["kind"],
        "canonical_key": row["canonical_key"],
        "name": row["name"],
        "metadata": json.loads(row["metadata_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _teaching_row(row: sqlite3.Row) -> dict[str, Any]:
    keys = row.keys()
    return {
        "id": row["id"],
        "entity_id": row["entity_id"],
        "entity_name": row["entity_name"] if "entity_name" in keys else None,
        "entity_kind": row["entity_kind"] if "entity_kind" in keys else None,
        "domain": row["domain"],
        "teaching_kind": row["teaching_kind"],
        "payload": json.loads(row["payload_json"]),
        "source": row["source"],
        "created_at": row["created_at"],
    }


def upsert_entity(
    *,
    kind: str,
    canonical: str,
    name: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    kind_key = canonicalize(kind)
    canonical_key = canonicalize(canonical)
    if not kind_key or not canonical_key or not name.strip():
        raise ValueError("entity kind, canonical key, and name are required")

    entity_id = stable_id("ent", f"{kind_key}|{canonical_key}")
    now = utc_now()
    metadata_json = _json(metadata or {})

    with connect() as db:
        db.execute(
            """
            INSERT INTO entities
                (id, kind, canonical_key, name, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(kind, canonical_key) DO UPDATE SET
                name = excluded.name,
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                entity_id,
                kind_key,
                canonical_key,
                name.strip(),
                metadata_json,
                now,
                now,
            ),
        )
        row = db.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()

    return _entity_row(row)


def teach(
    *,
    entity_kind: str,
    canonical: str,
    name: str,
    domain: str,
    teaching_kind: str,
    payload: dict[str, Any],
    source: str = "human",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("teaching payload must be a non-empty object")

    entity = upsert_entity(
        kind=entity_kind,
        canonical=canonical,
        name=name,
        metadata=metadata,
    )

    normalized_domain = canonicalize(domain)
    normalized_kind = canonicalize(teaching_kind)
    source = source.strip() or "human"

    payload_json = _json(payload)
    fingerprint_source = "|".join(
        [
            entity["id"],
            normalized_domain,
            normalized_kind,
            payload_json,
            canonicalize(source),
        ]
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    teaching_id = stable_id("teach", fingerprint)
    now = utc_now()

    duplicate = False

    with connect() as db:
        existing = db.execute(
            "SELECT id FROM teachings WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()

        if existing:
            duplicate = True
        else:
            db.execute(
                """
                INSERT INTO teachings
                    (id, entity_id, domain, teaching_kind, payload_json,
                     fingerprint, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    teaching_id,
                    entity["id"],
                    normalized_domain,
                    normalized_kind,
                    payload_json,
                    fingerprint,
                    source,
                    now,
                ),
            )
            db.commit()

    if not duplicate:
        append_event(
            timeline_event(
                stream=normalized_domain or "world",
                kind=f"teaching.{normalized_kind}",
                source=source,
                unit="iso8601",
                value=now,
                payload={
                    "teaching_id": teaching_id,
                    "entity_id": entity["id"],
                    "entity_kind": entity["kind"],
                    "entity_name": entity["name"],
                    "teaching_kind": normalized_kind,
                    "teaching": payload,
                },
            )
        )

    return {
        "ok": True,
        "duplicate": duplicate,
        "entity": entity,
        "teaching_id": teaching_id,
        "message": (
            "already knew this exact teaching"
            if duplicate
            else "learned a new version"
        ),
    }


def list_entities(kind: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    with connect() as db:
        if kind:
            rows = db.execute(
                """
                SELECT * FROM entities
                WHERE kind = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (canonicalize(kind), limit),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT * FROM entities
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_entity_row(row) for row in rows]


def list_teachings(
    *,
    entity_id: str | None = None,
    domain: str | None = None,
    teaching_kind: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    clauses: list[str] = []
    values: list[Any] = []

    if entity_id:
        clauses.append("t.entity_id = ?")
        values.append(entity_id)
    if domain:
        clauses.append("t.domain = ?")
        values.append(canonicalize(domain))
    if teaching_kind:
        clauses.append("t.teaching_kind = ?")
        values.append(canonicalize(teaching_kind))

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    values.append(limit)

    with connect() as db:
        rows = db.execute(
            f"""
            SELECT
                t.*,
                e.name AS entity_name,
                e.kind AS entity_kind
            FROM teachings t
            JOIN entities e ON e.id = t.entity_id
            {where}
            ORDER BY t.created_at DESC
            LIMIT ?
            """,
            values,
        ).fetchall()

    return [_teaching_row(row) for row in rows]


def stats() -> dict[str, Any]:
    with connect() as db:
        entity_count = db.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        teaching_count = db.execute("SELECT COUNT(*) FROM teachings").fetchone()[0]
        domains = [
            {"domain": row[0], "count": row[1]}
            for row in db.execute(
                """
                SELECT domain, COUNT(*)
                FROM teachings
                GROUP BY domain
                ORDER BY COUNT(*) DESC, domain
                """
            ).fetchall()
        ]
        kinds = [
            {"kind": row[0], "count": row[1]}
            for row in db.execute(
                """
                SELECT kind, COUNT(*)
                FROM entities
                GROUP BY kind
                ORDER BY COUNT(*) DESC, kind
                """
            ).fetchall()
        ]

    return {
        "entities": entity_count,
        "teachings": teaching_count,
        "domains": domains,
        "entity_kinds": kinds,
        "database": str(world_db_path()),
    }
