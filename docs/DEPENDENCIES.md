# Dependency notes

The release targets Python 3.12/3.13 and Node 22 on CPU-only local machines.

## Computer vision

- **OpenCV** provides `FaceDetectorYN` and `FaceRecognizerSF`.
- **YuNet** (`face_detection_yunet_2023mar.onnx`) is sourced from OpenCV Zoo. The model directory is MIT-licensed. The OpenCV Zoo Git LFS pointer records SHA-256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`.
- **SFace** (`face_recognition_sface_2021dec.onnx`) is sourced from OpenCV Zoo. The model directory is Apache-2.0. The OpenCV Zoo Git LFS pointer records SHA-256 `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`.

OpenCV Zoo's current YuNet documentation notes that the 2023 model remains the stable OpenCV 4.x path; the 2026 dynamic-input export specifically targets the OpenCV 5.x ONNX Runtime engine. This project therefore uses the 2023 model for the 4.x/CPU target.

## Clustering

scikit-learn DBSCAN is used because the number of persona clusters is unknown and noise points can remain unassigned.

## API

FastAPI provides the local REST API and WebSocket endpoint used for import progress.

## Frontend

React/Vite render the application. `@xyflow/react` provides graph panning, zooming, selection, custom nodes, controls, and progressive neighborhood exploration.

## Model acquisition

`python scripts/fetch_models.py` is the only default command that requires internet access. It downloads the two model files from the OpenCV Hugging Face mirrors and verifies the OpenCV-published SHA-256 values before accepting them.
