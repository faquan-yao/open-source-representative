#!/usr/bin/env bash
# Export Marp slides to PNG images (macOS/Linux)
# Usage: export-slide-images.sh path/to/slides.marp.md [output_dir]

set -euo pipefail

MARP_FILE="${1:?Usage: export-slide-images.sh <slides.marp.md> [output_dir]}"
OUTPUT_DIR="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TECHNOLOGY_DIR="$(dirname "$SKILL_DIR")"
THEME_DIR="$TECHNOLOGY_DIR/document-to-presentation/templates/theme"

PPT_DIR="$(dirname "$MARP_FILE")"
if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$PPT_DIR/video/slides"
fi

VIDEO_DIR="$(dirname "$OUTPUT_DIR")"
mkdir -p "$OUTPUT_DIR"
OUTPUT_PREFIX="$VIDEO_DIR/slides"

echo "[INFO] Converting: $MARP_FILE"
echo "[INFO] Output dir: $OUTPUT_DIR"
echo "[INFO] Theme:      $THEME_DIR"

npx --yes @marp-team/marp-cli "$MARP_FILE" \
  --images png \
  -o "$OUTPUT_PREFIX" \
  --no-stdin \
  --theme-set "$THEME_DIR"

shopt -s nullglob
raw=( "$VIDEO_DIR"/slides.* )
if [[ ${#raw[@]} -eq 0 ]]; then
  echo "[ERROR] No slide images under $VIDEO_DIR" >&2
  exit 1
fi

i=1
for img in $(printf '%s\n' "${raw[@]}" | sort); do
  printf -v dest "%s/%03d.png" "$OUTPUT_DIR" "$i"
  cp "$img" "$dest"
  i=$((i + 1))
done

count="$(find "$OUTPUT_DIR" -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')"
echo "[OK] Normalized $count slide images to $OUTPUT_DIR"
