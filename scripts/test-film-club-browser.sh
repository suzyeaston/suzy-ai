#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [[ -z "$CHROME" ]]; then
  echo "Chrome/Chromium required for real Web Audio offline smoke." >&2
  exit 1
fi
PORT=18863
python3 -m http.server "$PORT" --bind 127.0.0.1 >/tmp/suzy-film-browser-http.log 2>&1 &
HTTP_PID=$!
cleanup(){ kill "$HTTP_PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 1
OUT="$(mktemp)"
trap 'rm -f "$OUT"; cleanup' EXIT
timeout 60 "$CHROME" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --no-first-run --virtual-time-budget=25000 --dump-dom \
  "http://127.0.0.1:$PORT/tests/film_club_browser_smoke.html" >"$OUT" 2>/tmp/suzy-film-browser-chrome.log || {
  cat /tmp/suzy-film-browser-chrome.log >&2
  exit 1
}
if grep -q 'data-result="PASS"' "$OUT"; then
  echo "Real Chrome OfflineAudioContext score rendering: PASS"
  sed -n '/data-result="PASS"/p' "$OUT" | cut -c 1-320
else
  echo "Chrome Web Audio smoke FAILED" >&2
  sed -n '/data-result=/p' "$OUT" | cut -c 1-1500 >&2
  cat /tmp/suzy-film-browser-chrome.log >&2
  exit 1
fi
