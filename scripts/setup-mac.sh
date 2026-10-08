#!/usr/bin/env bash
# Explicit one-time setup. Run from a downloaded/cloned SUZY//AI checkout.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo 'This setup requires a Mac running natively on Apple Silicon (not Rosetta).' >&2
  exit 1
fi
printf '%s\n' 'SUZY//AI setup: Python, llama.cpp, and a verified 1.28 GB local model.'
printf '%s\n' 'Allow several GB of free disk space for tools and the model. No personal data is uploaded.'
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
export HOMEBREW_NO_ANALYTICS=1
export HOMEBREW_NO_AUTO_UPDATE=1
if ! command -v brew >/dev/null 2>&1; then
  echo 'Installing Homebrew from its official installer. macOS may ask for your password.'
  installer="$(mktemp -t suzy-homebrew)"
  trap 'rm -f "$installer"' EXIT
  curl --fail --location --proto '=https' --proto-redir '=https' \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer"
  /bin/bash "$installer"
  rm -f "$installer"
  trap - EXIT
fi
brew install python@3.12 llama.cpp
PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
# Dedicated environment; never remove or rebuild a user's existing .venv.
if [[ ! -d .venv-mac ]]; then
  "$PYTHON" -m venv .venv-mac
fi
.venv-mac/bin/python -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required"'
.venv-mac/bin/python -m pip install -e .
.venv-mac/bin/python -m unittest discover -s tests -q
.venv-mac/bin/python -m suzy_ai.local_runtime download
printf '\n%s\n' 'Setup complete. Start SUZY//AI with:'
printf '  cd %q && bash scripts/start-mac.sh\n' "$ROOT"
