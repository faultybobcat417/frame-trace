#!/usr/bin/env bash
set -euo pipefail

ZIP="${1:-}"
if [ -z "$ZIP" ]; then
  ZIP="$(find "$HOME/Downloads" "$HOME/Desktop" -maxdepth 1 -type f -name 'frame-trace-v1.0.0*.zip' -print 2>/dev/null | sort | tail -1)"
fi
if [ -z "${ZIP:-}" ] || [ ! -f "$ZIP" ]; then
  echo "frame-trace-v1.0.0.zip not found in Downloads/Desktop" >&2
  exit 2
fi
unzip -t "$ZIP" >/dev/null
WORK="$HOME/Desktop/frame-trace-local-test"
rm -rf "$WORK"
mkdir -p "$WORK"
unzip -q "$ZIP" -d "$WORK"
cd "$WORK/frame-trace"
PYTHON="$(command -v python3.12 || command -v python3)"
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
(cd frontend && npm install)
frame-trace doctor
frame-trace demo
frame-trace evaluate
pytest
python -m compileall -q backend
(cd frontend && npm run typecheck && npm test && npm run build)
printf '\nFRAME TRACE — LOCAL CORE VERIFICATION PASSED\n'
printf 'Optional CV gate: python scripts/fetch_models.py && frame-trace import /absolute/path/to/authorized-media\n'
