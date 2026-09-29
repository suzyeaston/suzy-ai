#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf '\033[36m→\033[0m %s\n' "$*"; }
ok()  { printf '\033[32m✓\033[0m %s\n' "$*"; }
warn(){ printf '\033[33m!\033[0m %s\n' "$*"; }

find_python() {
  local candidate
  for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON="$(find_python || true)"

if [[ -n "$PYTHON" ]]; then
  VERSION="$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  ok "Found Python ${VERSION}: ${PYTHON}"

  if [[ -x .venv/bin/python ]]; then
    if ! .venv/bin/python - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
    then
      warn "Old .venv detected. Rebuilding generated environment."
      rm -rf .venv
    fi
  fi

  if [[ ! -d .venv ]]; then
    say "Creating isolated Python environment…"
    "$PYTHON" -m venv .venv
  fi

  source .venv/bin/activate
  python -m pip install --upgrade pip setuptools wheel >/dev/null
  python -m pip install -e .

else
  say "Python 3.11+ not found. Using uv to provide a managed Python runtime."

  if ! command -v uv >/dev/null 2>&1; then
    say "Installing uv from Astral's official standalone installer…"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Make the freshly installed binary visible without opening a new Terminal.
    export PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    echo
    echo "uv installed but is not visible in this Terminal."
    echo "Open a new Terminal and rerun:"
    echo "  cd ~/Projects/suzy-ai"
    echo "  ./scripts/bootstrap-local.sh"
    exit 1
  fi

  ok "uv ready: $(uv --version)"

  # uv can download the managed Python automatically.
  say "Creating .venv with managed CPython 3.12…"
  rm -rf .venv
  uv venv --python 3.12 .venv

  say "Installing SUZY//AI into the managed environment…"
  uv pip install --python .venv/bin/python -e .

  source .venv/bin/activate
fi

suzy-ai init

echo
ok "SUZY//AI local core ready"
echo "Python: $(python --version 2>&1)"
echo
echo "Try:"
echo "  source .venv/bin/activate"
echo "  suzy-ai doctor"
echo "  suzy-ai serve"
