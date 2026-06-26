#!/usr/bin/env bash
# Export Marp markdown to PPTX (macOS/Linux)
# Usage: export-pptx.sh path/to/slides.marp.md [path/to/out.pptx]

set -euo pipefail

MARP_FILE="${1:?Usage: export-pptx.sh <slides.marp.md> [output.pptx]}"
OUTPUT_FILE="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$SKILL_DIR/templates/theme"

if [[ -z "$OUTPUT_FILE" ]]; then
  OUTPUT_FILE="${MARP_FILE%.marp.md}.pptx"
  OUTPUT_FILE="${OUTPUT_FILE%.md}.pptx"
fi

echo "[INFO] Converting: $MARP_FILE"
echo "[INFO] Output:     $OUTPUT_FILE"
echo "[INFO] Theme:      $THEME_DIR"

npx --yes @marp-team/marp-cli "$MARP_FILE" \
  --pptx \
  -o "$OUTPUT_FILE" \
  --no-stdin \
  --theme-set "$THEME_DIR"

echo "[OK] Created $OUTPUT_FILE"
