#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != Darwin ]]; then
  echo 'This companion requires macOS 13+ and Xcode Command Line Tools.' >&2; exit 1
fi
command -v swift >/dev/null || { echo 'Install Xcode Command Line Tools with xcode-select --install.' >&2; exit 1; }
cd "$ROOT/apps/macos"
swift build -c release
BIN="$(swift build -c release --show-bin-path)"
APP="$ROOT/build/SuzyLive.app"
mkdir -p "$APP/Contents/MacOS"
cp "$BIN/SuzyLive" "$APP/Contents/MacOS/SuzyLive"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>SuzyLive</string>
<key>CFBundleIdentifier</key><string>ca.suzyeaston.suzylive</string>
<key>CFBundleName</key><string>Suzy Live</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>LSMinimumSystemVersion</key><string>13.0</string>
<key>NSMicrophoneUsageDescription</key><string>Capture your guitar or voice to create a musical response you can audition.</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
PLIST
plutil -lint "$APP/Contents/Info.plist"
codesign --force --sign - "$APP"
echo "Built $APP"
