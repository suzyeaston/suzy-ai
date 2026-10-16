#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
binary="$(mktemp -t suzy-loop-test.XXXXXX)"
trap 'rm -f "$binary"' EXIT
frameworks=()
if [[ "$(uname -s)" == Darwin ]]; then frameworks=(-framework CoreAudio -framework AudioToolbox); fi
cc -std=c11 -Wall -Wextra -Werror -g -fsanitize=address,undefined \
  -I apps/macos/Sources/NativeLoop/include \
  apps/macos/Sources/NativeLoop/Loop.c tests/native/test_loop.c \
  "${frameworks[@]}" -lm -o "$binary"
"$binary"
