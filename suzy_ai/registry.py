from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_registry() -> dict[str, Any]:
    return json.loads((ROOT / "config" / "apps.json").read_text(encoding="utf-8"))
