#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_DIR="${ANDROID_HOME:-/opt/homebrew/share/android-commandlinetools}"
NDK_DIR="${ANDROID_NDK_HOME:-$SDK_DIR/ndk/27.2.12479018}"
CLANG="$NDK_DIR/toolchains/llvm/prebuilt/darwin-x86_64/bin/armv7a-linux-androideabi34-clang++"
OUT="$ROOT_DIR/dist/native/xgimi-pq-tool-armeabi-v7a"

mkdir -p "$(dirname "$OUT")"

"$CLANG" \
  -std=c++17 \
  -Wall \
  -Wextra \
  -Werror \
  -fPIE \
  -pie \
  "$ROOT_DIR/native/xgimi-pq-tool.cpp" \
  -o "$OUT" \
  -lbinder_ndk \
  -ldl \
  -llog

echo "$OUT"
