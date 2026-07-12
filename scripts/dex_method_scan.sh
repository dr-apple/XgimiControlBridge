#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <dexdump-text-or-directory> [more paths...]" >&2
  exit 2
fi

patterns='PqModeManager|DatabaseHelper|ColorSpaceManager|GM_DISP_SCENE_V3|setPictureMode|setHdr|Hdr HDR10|mHdrType|setMemc|setMfc|setColorTemp|setGamma|setBrightness|AiPicture|AIPQ|Keystone|Autofocus|Focus|Zoom|ConfigurationService|OpAppInitialService'

for input in "$@"; do
  if [ -d "$input" ]; then
    find "$input" -type f \( -name '*.dump' -o -name '*.txt' \) -print0
  else
    printf '%s\0' "$input"
  fi
done | while IFS= read -r -d '' file; do
  echo "===== $file"
  grep -Eain "$patterns" "$file" || true
done
