# Demo modes

Frame Trace keeps two forms of evidence separate.

## Deterministic logic fixture

`frame-trace demo` creates:

- 6 anonymous personas;
- 4 fictional source accounts;
- 20 synthetic asset records;
- repeated appearances and co-occurrences;
- 2 deliberately uncertain review items;
- deterministic normalized vectors with ground truth for clustering evaluation.

The SVG persona portraits are UI fixtures. They are not presented as output from YuNet or SFace.

## Real CV path

After `python scripts/fetch_models.py`, the YuNet/SFace adapters can process local user-authorized images and videos. The repository does not ship real people's photos and does not download random face datasets.

This split makes the recruiter demo deterministic while keeping the actual CV boundary executable and independently testable on authorized input.
