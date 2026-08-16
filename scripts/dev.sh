#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
frame-trace demo >/dev/null
trap 'kill 0' EXIT
frame-trace serve &
(cd frontend && npm run dev) &
wait
