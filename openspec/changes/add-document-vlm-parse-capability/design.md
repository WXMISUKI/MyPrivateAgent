## Design Summary

`document.vlm.parse` provides semantic document understanding, not plain OCR extraction.

Input envelope:
- `file_base64`, `media_type`, `filename`
- `task` (`summarize`, `extract_fields`, `chart_understanding`, `qa`)
- optional `question`, `schema_hint`, `max_pages`

Output envelope:
- `summary`
- `sections[]`
- `entities[]`
- `answers[]`
- `evidence[]`
- `warnings[]`
- `raw`

## Boundaries

- External provider owns VLM models and inference runtime.
- Main backend does not import VLM frameworks or model weights.
- First slice is synchronous for small files; async job mode is a separate follow-up change.

## Verification

- Backend contract and error-shape tests for VLM invoke/health.
- Frontend diagnostics rendering tests for semantic output fields.
