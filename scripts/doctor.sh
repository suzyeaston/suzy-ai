#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x .venv/bin/suzy-ai ]]; then
  source .venv/bin/activate
  suzy-ai doctor
else
  echo "SUZY//AI virtual environment not installed."
  echo "Run ./scripts/bootstrap-local.sh"
  exit 1
fi
