# Verification

Frame Trace was verified locally on Apple Silicon macOS with the real computer-vision path enabled.

## Environment

- Python 3.12.13
- arm64
- OpenCV 4.14.0
- NumPy 2.5.2
- YuNet and SFace model files checksum-verified before inference

## Deterministic system verification

- backend tests: **14 passed**
- frontend typecheck: **PASS**
- Vitest: **1 passed**
- Vite production build: **PASS**
- Playwright golden flow: **1 passed**
- deterministic fixture: **6 personas**, **20 assets**, **30 detections**, **2 review items**
- pairwise precision: **1.0**
- pairwise recall: **1.0**
- pairwise F1: **1.0**
- Adjusted Rand Index: **1.0**
- abstention rate: **5.26%**
- false-merge pairs: **0**
- false-split pairs: **0**

## Real CV smoke test

The real local pipeline was exercised with a local test image and a derived visual variant. No test image is included in this repository.

- YuNet detections: **1 + 1**
- detector confidence: **0.9348 / 0.9343**
- SFace embedding dimension: **128**
- embedding norms: **1.0 / 1.0**
- derived-pair cosine similarity: **0.988860**
- direct CV smoke: **PASS**

The same pair was then processed through the end-to-end import path:

- assets: **2**
- frames: **2**
- detections: **2**
- embeddings: **2**
- personas: **1**
- memberships: **2**
- appearances: **2**
- real import smoke: **PASS**

The repository does not include the local test image, downloaded model weights, application data, virtual environments, frontend dependencies, or build artifacts.

## Model checksums

```text
YuNet  face_detection_yunet_2023mar.onnx
8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4

SFace  face_recognition_sface_2021dec.onnx
0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79
```

Run `./scripts/verify_release.sh` for the reproducible deterministic release gates. The real CV path additionally requires `python scripts/fetch_models.py` and user-supplied local media.
