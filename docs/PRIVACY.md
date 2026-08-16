# Privacy boundary

Frame Trace is a media-corpus organization tool, not an identity lookup service.

It accepts only media deliberately supplied to the local application. A recurring visual cluster receives an anonymous identifier such as `P014`. The software does not search the public internet for a face, discover social accounts, attach government or real-world identity, connect to camera networks, or infer sensitive traits.

A user may add a local label to their own cluster. That label is user-provided metadata and is never inferred by the system.

The UI uses the phrase **co-occurs with** for shared media because the underlying evidence cannot establish a social or professional relationship.

The application contains no telemetry, analytics beacon, cloud upload, or remote recognition API. Network access is limited to the explicit model-fetch command described in `docs/DEPENDENCIES.md`.
