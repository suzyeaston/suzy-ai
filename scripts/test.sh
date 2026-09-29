#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 -m suzy_ai.cli --version
