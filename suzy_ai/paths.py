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
    project = Path(__file__).resolve().parents[1]
    if (project / ".git").exists() and root.is_relative_to(project):
        raise ValueError("SUZY_AI_HOME must be outside the source repository")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
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
        (root / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    return root
