# Methodology

## Detection and representation

The production CV adapter is designed around OpenCV's `FaceDetectorYN` with YuNet and `FaceRecognizerSF` with SFace. Five detector landmarks are passed to SFace alignment before feature extraction. Embeddings are L2-normalized before similarity or clustering.

## Similarity

For normalized embeddings `x` and `y`, Frame Trace uses cosine similarity:

`similarity(x, y) = x · y`

The default in-memory index performs exact matrix multiplication. Approximate nearest-neighbor infrastructure is deliberately excluded from the required path because the local corpus is small.

## Clustering

The number of people is not known ahead of time, so the reference clustering engine uses DBSCAN with cosine distance. DBSCAN can emit noise instead of forcing every detection into a cluster.

A second consistency gate checks similarity to a cluster medoid. A weak member becomes `review_required` or `unassigned`; it is not silently forced into a persona.

False merges are treated as more damaging than abstention. The thresholds in `frame_trace.config.Settings` are centralized and are heuristics, not probabilities of real identity.

## Appearance aggregation

An image produces a single appearance per accepted persona. Video processing samples frames at a configured interval and records frame timestamps. Continuous detections can be collapsed into time-bounded appearance segments. Raw detections remain available for provenance and review.

## Co-occurrence

Two personas co-occur when accepted appearances share the same image asset or overlap in a video interval. A co-occurrence edge means only that the two anonymous persona clusters were observed in the same imported media; it does not imply friendship, employment, association, or any other real-world relationship.

## Evaluation fixture

The bundled demo is a deterministic logic fixture: six synthetic anonymous persona centers produce normalized vectors with controlled noise, plus two deliberately isolated vectors. This fixture tests clustering, abstention, persistence, review, graph projection, and UI behavior without claiming that its vectors came from SFace.

Real CV is a separate adapter path and requires checksum-verified YuNet/SFace model artifacts plus user-authorized media.
