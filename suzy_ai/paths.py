from __future__ import annotations

import os
from pathlib import Path


def home() -> Path:
    raw = os.environ.get("SUZY_AI_HOME")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / ".suzy-ai"


def ensure_home() -> Path:
    root = home()
    for name in (
        "memory",
        "world",
        "models",
        "cache",
        "recordings",
        "training-data",
        "research",
        "logs",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root
