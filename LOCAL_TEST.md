# Local verification on macOS

Target: Apple Silicon, Python 3.12, Node 22+.

```bash
unzip frame-trace-v1.0.0.zip
cd frame-trace

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'

cd frontend
npm install
cd ..

frame-trace doctor
frame-trace demo
frame-trace evaluate
pytest
python -m compileall -q backend

cd frontend
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run e2e
```

Optional real-CV gate:

```bash
cd ..
source .venv/bin/activate
python scripts/fetch_models.py
frame-trace doctor
frame-trace import /absolute/path/to/authorized-media
```

The deterministic demo and the real-CV import path are intentionally separate. The demo never pretends its synthetic vectors were produced by SFace.
