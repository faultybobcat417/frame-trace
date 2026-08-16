#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/../frame-trace-v1.0.0.zip}"
cd "$(dirname "$ROOT")"
rm -f "$OUT"
zip -qr "$OUT" "$(basename "$ROOT")" \
  -x '*/.git/*' '*/.venv/*' '*/node_modules/*' '*/__pycache__/*' '*/.pytest_cache/*' \
     '*/frontend/dist/*' '*/models/weights/*' '*/data/*' '*.DS_Store'
unzip -t "$OUT" >/dev/null
printf '%s\n' "$OUT"
