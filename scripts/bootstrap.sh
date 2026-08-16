#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
if command -v npm >/dev/null 2>&1; then
  (cd frontend && npm install)
else
  echo "npm not found; frontend dependencies were not installed" >&2
fi
python scripts/fetch_models.py || echo "Model download unavailable; deterministic demo remains usable."
frame-trace doctor
