from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import ensure_home


def timeline_path() -> Path:
    return ensure_home() / "world" / "timeline.jsonl"


def append_event(event: dict[str, Any]) -> None:
    path = timeline_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_events(stream: str | None = None) -> list[dict[str, Any]]:
    path = timeline_path()
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if stream is None or item.get("stream") == stream:
            events.append(item)
    return events
