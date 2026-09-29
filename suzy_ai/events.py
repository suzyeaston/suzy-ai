from __future__ import annotations

import datetime as dt
import uuid
from typing import Any


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def timeline_event(
    *,
    stream: str,
    kind: str,
    source: str,
    unit: str,
    value: str | float,
    payload: dict[str, Any],
    confidence: float | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "id": str(uuid.uuid4()),
        "stream": stream,
        "kind": kind,
        "source": source,
        "created_at": utc_now(),
        "position": {
            "unit": unit,
            "value": value,
        },
        "duration": None,
        "payload": payload,
        "confidence": confidence,
        "provenance": {
            "mode": "local"
        },
    }
