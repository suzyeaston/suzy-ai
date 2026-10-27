#!/usr/bin/env bash
# Compile the small native AU host once; leave the existing Logic/MRT2 install alone.
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Magenta Audio Unit hosting requires macOS." >&2; exit 1
fi
cd "$(dirname "$0")/.."
mkdir -p .build
if [[ ! -x ".build/toaster-magenta-host" || apps/toaster-magenta/ToasterMagentaHost.swift -nt .build/toaster-magenta-host ]]; then
  echo "Compiling TOASTER's local Magenta AU bridge..."
  xcrun swiftc -O -framework AVFoundation -framework AudioToolbox \
    apps/toaster-magenta/ToasterMagentaHost.swift \
    -o .build/toaster-magenta-host
fi
echo "Native MRT2 bridge compiled. Start TOASTER with:"
echo "  .venv-mac/bin/python -m suzy_ai.music.magenta_stage"
echo "Then click ENABLE MAGENTA in TOASTER."
echo "MRT2 Small must already be installed. Optional override: export SUZY_MRT2_MODEL=/path/to/mrt2_small.mlxfn"
