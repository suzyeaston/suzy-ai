#!/usr/bin/env bash
# Pair Apple's swiftc with a matching SDK. Never mix Swift 6.3 with SDK 6.4.
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Native MRT2 host compilation requires macOS." >&2; exit 1
fi
cd "$(dirname "$0")/.."
mkdir -p .build
swift_src="apps/toaster-magenta/ToasterMagentaHost.swift"
native_out=".build/toaster-magenta-host"
sdk_version() {
  local sdk="$1" interface=""
  # SDK Swift interface records the compiler that produced it.
  interface="$(find "$sdk/usr/lib/swift/Swift.swiftmodule" -maxdepth 1 -name '*macos.swiftinterface' -print -quit 2>/dev/null || true)"
  if [[ -n "$interface" ]]; then
    sed -nE 's@^// swift-compiler-version: Apple Swift version ([0-9]+\.[0-9]+).*@\1@p' "$interface" | head -1
  fi
}
tool_version() {
  "$1" -version 2>/dev/null | sed -nE 's@^Apple Swift version ([0-9]+\.[0-9]+).*@\1@p' | head -1
}
try_pair() {
  local swift="$1" sdk="$2" sv av
  [[ -x "$swift" && -d "$sdk" ]] || return 1
  sv="$(tool_version "$swift")"; av="$(sdk_version "$sdk")"
  [[ -n "$sv" && -n "$av" && "$sv" == "$av" ]] || return 1
  SWIFTC="$swift"; SDK="$sdk"; return 0
}
SWIFTC="" SDK=""
devroot="$(xcode-select -p 2>/dev/null || true)"
# Prefer the currently selected coherent Xcode/toolchain pair.
if [[ -n "$devroot" ]]; then
  swift="$(xcrun --find swiftc 2>/dev/null || true)"
  sdk="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null || true)"
  try_pair "$swift" "$sdk" || true
fi
# If CLT has mismatched SDK (the user's exact error), try a different
# installed Xcode, or an older CLT SDK compiled with the same Swift version.
if [[ -z "$SWIFTC" ]]; then
  for developer in /Applications/Xcode.app/Contents/Developer /Applications/Xcode-beta.app/Contents/Developer; do
    [[ -d "$developer" ]] || continue
    swift="$(DEVELOPER_DIR="$developer" xcrun --find swiftc 2>/dev/null || true)"
    sdk="$(DEVELOPER_DIR="$developer" xcrun --sdk macosx --show-sdk-path 2>/dev/null || true)"
    try_pair "$swift" "$sdk" && break
  done
fi
if [[ -z "$SWIFTC" ]]; then
  swift="$(xcrun --find swiftc 2>/dev/null || true)"
  for sdk in /Library/Developer/CommandLineTools/SDKs/MacOSX26*.sdk /Library/Developer/CommandLineTools/SDKs/MacOSX15*.sdk; do
    [[ -d "$sdk" ]] || continue
    try_pair "$swift" "$sdk" && break
  done
fi
if [[ -z "$SWIFTC" ]]; then
  echo "TOASTER native build stopped: Apple's Swift compiler and macOS SDK do not match." >&2
  echo "Your report: Swift 6.3.3 vs macOS 27 SDK built with Swift 6.4." >&2
  echo "Install/select Xcode with a compatible compiler+SDK pair, or install matching Command Line Tools." >&2
  echo "Try: xcode-select -p; xcrun swiftc -version; xcrun --show-sdk-path" >&2
  echo "This script won't patch Apple's SDK or download a model." >&2
  exit 2
fi
if [[ ! -x "$native_out" || "$swift_src" -nt "$native_out" ]]; then
  echo "Compiling real MRT2 Audio Unit host with $SWIFTC"
  echo "Using matching SDK: $SDK"
  "$SWIFTC" -sdk "$SDK" -O -framework AVFoundation -framework AudioToolbox -framework AppKit \
    "$swift_src" -o "$native_out"
fi
echo "Native Magenta host built successfully."
echo "Start TOASTER: .venv-mac/bin/python -m suzy_ai.music.magenta_stage"
echo "The local mrt2_small .mlxfn model must already exist. No downloads are performed."
