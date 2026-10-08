#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
if [[ ! -x .venv-mac/bin/python ]]; then
  echo 'Run bash scripts/setup-mac.sh first.' >&2
  exit 1
fi
exec .venv-mac/bin/python -m suzy_ai.local_runtime run "$@"
