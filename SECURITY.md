# Security and privacy boundary

Frame Trace is local-first and processes only media explicitly supplied by the operator. The default application contains no telemetry, analytics beacon, cloud upload, remote face API, social-platform scraper, or public-internet identity lookup.

The model download script is the only network-dependent component in the default repository. It retrieves the two documented OpenCV model artifacts and refuses to continue if a SHA-256 checksum differs from `models/manifest.json`.

Manifest paths are resolved beneath the selected package root and path traversal is rejected. Imported media is treated as data, never executed.

Do not use Frame Trace to identify unknown people, search public profiles by face, connect to surveillance-camera networks, or infer sensitive personal attributes.
