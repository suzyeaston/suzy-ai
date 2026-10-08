"""Explicitly approved private notes, with lexical retrieval and provenance."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager

from .events import utc_now
from .paths import ensure_home


def text_field(value: object, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must be non-empty text, at most {maximum} characters")
    return value.strip()


@contextmanager
def connect():
    directory = ensure_home() / "memory"
    directory.chmod(0o700)
    path = directory / "memory.sqlite3"
    # Create with restrictive permissions before SQLite can write private content.
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.close(fd)
    path.chmod(0o600)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA secure_delete = ON")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL,
                source TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                title, text, content='documents', content_rowid='rowid'
            );
            CREATE TRIGGER IF NOT EXISTS documents_insert AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, title, text)
                VALUES (new.rowid, new.title, new.text);
            END;
            CREATE TRIGGER IF NOT EXISTS documents_delete AFTER DELETE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, text)
                VALUES ('delete', old.rowid, old.title, old.text);
            END;
        """)
        with db:
            yield db
    finally:
        db.close()


def add(*, title: str, text: str, source: str, approved: bool = False) -> dict:
    if approved is not True:
        raise ValueError("explicit approved=true is required to store memory")
    document = {
        "id": f"mem_{uuid.uuid4().hex}",
        "title": text_field(title, "title", 200),
        "text": text_field(text, "text", 20_000),
        "source": text_field(source, "source", 500),
        "created_at": utc_now(),
    }
    with connect() as db:
        db.execute("INSERT INTO documents (id,title,text,source,created_at) VALUES (?,?,?,?,?)",
                   tuple(document.values()))
    return document


def search(query: str, limit: int = 5, max_chars: int = 6000) -> list[dict]:
    query = text_field(query, "query", 8000)
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError("limit must be an integer from 1 to 10")
    if type(max_chars) is not int or not 1 <= max_chars <= 12000:
        raise ValueError("max_chars must be an integer from 1 to 12000")
    # Quote individual Unicode word tokens: caller input is never FTS syntax or SQL.
    tokens = list(dict.fromkeys(re.findall(r"\w+", query.casefold())))[:32]
    if not tokens:
        return []
    expression = " OR ".join('"' + token + '"' for token in tokens)
    with connect() as db:
        rows = db.execute("""
            SELECT d.*, bm25(documents_fts, 2.0, 1.0) AS score,
                   snippet(documents_fts, 1, '', '', ' … ', 48) AS excerpt
            FROM documents_fts JOIN documents d ON d.rowid = documents_fts.rowid
            WHERE documents_fts MATCH ? ORDER BY score, d.id LIMIT ?
        """, (expression, limit)).fetchall()
    results = []
    remaining = max_chars
    for row in rows:
        item = {key: row[key] for key in ("id", "title", "source", "created_at")}
        item["excerpt"] = row["excerpt"][:2000]
        # Budget the entire serialized source, including metadata and escaping.
        size = len(json.dumps(item, ensure_ascii=False))
        if size > remaining:
            continue
        results.append(item)
        remaining -= size
    return results


def delete(document_id: str) -> bool:
    document_id = text_field(document_id, "id", 100)
    with connect() as db:
        deleted = db.execute("DELETE FROM documents WHERE id = ?", (document_id,)).rowcount
        # Rebuild removes stale text from the FTS index. Backups remain independent.
        if deleted:
            db.execute("INSERT INTO documents_fts(documents_fts) VALUES ('rebuild')")
    return bool(deleted)
