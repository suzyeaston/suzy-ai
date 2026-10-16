#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$ROOT/scripts/build-mac-companion.sh"
if [[ -n "${SUZY_PYTHON:-}" ]]; then
  PYTHON="$SUZY_PYTHON"
elif [[ -x "$ROOT/.venv-mac/bin/python" ]]; then
  PYTHON="$ROOT/.venv-mac/bin/python"
else
  PYTHON=python3
fi
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
cd "$ROOT"
BRIDGE_PID=''
cleanup() {
  if [[ -n "$BRIDGE_PID" ]]; then kill "$BRIDGE_PID" 2>/dev/null || true; wait "$BRIDGE_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM
# Reuse a recognized bridge; refuse to replace an unrelated listener.
STATE="$("$PYTHON" - <<'PY'
import http.client, json
try:
    c=http.client.HTTPConnection('127.0.0.1',7333,timeout=2)
    c.request('GET','/health'); r=c.getresponse(); raw=r.read(4097)
    p=json.loads(raw) if len(raw)<=4096 else {}
    print('ready' if r.status==200 and p.get('experimental') is True and p.get('audio_device_access') is False else 'occupied')
except ConnectionRefusedError:
    print('free')
except Exception:
    print('occupied')
PY
)"
if [[ "$STATE" == occupied ]]; then echo 'Port 7333 is occupied by an unrecognized service. Nothing was stopped.' >&2; exit 1; fi
if [[ "$STATE" == free ]]; then
  "$PYTHON" -m suzy_ai.music.server --port 7333 &
  BRIDGE_PID=$!
fi
"$PYTHON" - <<'PY'
import http.client, time
for _ in range(30):
    try:
        c=http.client.HTTPConnection('127.0.0.1',7333,timeout=1)
        c.request('GET','/health'); r=c.getresponse(); r.read(4096); c.close()
        if r.status==200: break
    except OSError: pass
    time.sleep(.1)
else: raise SystemExit('Bridge did not become ready.')
PY
echo 'Opening Suzy Live. Keep this terminal open. Quit the app to stop a bridge started by this script.'
echo 'Deterministic mode needs no model. Local model mode uses your existing core on port 7332.'
open -W "$ROOT/build/SuzyLive.app"
