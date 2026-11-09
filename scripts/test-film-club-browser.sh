#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [[ -z "$CHROME" ]]; then
  echo "Chrome/Chromium required for the real Web Audio smoke." >&2
  exit 1
fi
node scripts/test-film-club-browser.cjs "$CHROME"
