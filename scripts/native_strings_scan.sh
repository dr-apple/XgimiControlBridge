#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <library-or-directory> [more paths...]" >&2
  exit 2
fi

patterns='GM_DISP_SCENE_V3|PqModeManager|ColorSpaceManager|setPictureMode|PictureMode|HDR10|Hdr|MEMC|MFC|ColorTemp|Brightness|Gamma|AI|AIPQ|Zoom|Keystone|Focus|Binder|AIDL|descriptor'

for input in "$@"; do
  if [ -d "$input" ]; then
    find "$input" -type f \( -name '*.so' -o -name '*.apk' -o -name '*.jar' \) -print0
  else
    printf '%s\0' "$input"
  fi
done | while IFS= read -r -d '' file; do
  echo "===== $file"
  strings -a "$file" | grep -Eai "$patterns" | sort -u || true
done
