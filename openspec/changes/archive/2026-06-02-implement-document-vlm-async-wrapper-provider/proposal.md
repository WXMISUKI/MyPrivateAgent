## Why

`document.vlm.parse.async` is registered in MyPrivateAgent, but Stage 3B cannot be accepted because no local provider currently serves the configured async job API at `http://127.0.0.1:8082`.

We need a lightweight wrapper provider that can run independently from the main backend and expose the async job contract. This lets us validate submit/status lifecycle, polling behavior, provider heartbeat, and local sample acceptance before wiring a heavier PaddleOCR-VL runtime.

## What Changes

- Add a local development provider script for `document.vlm.parse.async`.
- Expose:
  - `GET /health`
  - `POST /api/vlm/jobs`
  - `GET /api/vlm/jobs/{job_id}`
- Execute jobs asynchronously in memory.
- Delegate actual document parsing to a configured upstream sync provider, defaulting to PP-StructureV3 `/layout-parsing`.
- Normalize job output to `job_id/status/progress/result/error/warnings/raw`.
- Document startup and acceptance commands for Stage 3B.

## Impact

- Adds an optional local provider utility under `backend/scripts/`.
- Does not change MyPrivateAgent capability runtime contract.
- Does not add heavy VLM/model dependencies to the main backend.
- Does not provide production persistence, distributed queueing, artifact storage, or GPU scheduling.
