#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <library-or-directory> [more paths...]" >&2
  exit 2
fi

patterns='picture|picmode|hdr|memc|mfc|colortemp|brightness|gamma|ai|pq|keystone|focus|zoom|binder|aidl|transaction|GM_DISP'

for input in "$@"; do
  if [ -d "$input" ]; then
    find "$input" -type f -name '*.so' -print0
  else
    printf '%s\0' "$input"
  fi
done | while IFS= read -r -d '' file; do
  echo "===== $file"
  if command -v llvm-nm >/dev/null 2>&1; then
    llvm-nm -C --defined-only "$file" 2>/dev/null | grep -Eai "$patterns" || true
  elif command -v nm >/dev/null 2>&1; then
    nm -C "$file" 2>/dev/null | grep -Eai "$patterns" || true
  else
    echo "No nm/llvm-nm found" >&2
    exit 1
  fi
done
