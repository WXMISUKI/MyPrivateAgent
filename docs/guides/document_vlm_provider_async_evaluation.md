# Document VLM Provider Integration and Async Evaluation

## Phase 3A Status

`document.vlm.parse` is now a contract-level placeholder capability in MyPrivateAgent.

- Registry toggle: `ENABLE_VLM_CAPABILITY_PROVIDER`
- Provider endpoint expectation:
  - `GET /health`
  - `POST /vlm`
- Provider-neutral result envelope:
  - `summary`, `sections`, `entities`, `answers`, `evidence`, `warnings`, `raw`

This phase is intentionally synchronous and limited to small files.

## Phase 3B Progress

Current provider adapter now supports two response families:

- direct VLM semantic envelope (`summary/sections/entities/answers/evidence`)
- PaddleOCR-VL-style envelope (`result.layoutParsingResults[]`) with normalized fallback extraction

Recommended PaddleOCR-VL integration config:

```env
ENABLE_VLM_CAPABILITY_PROVIDER=true
VLM_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8082
VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=120
VLM_CAPABILITY_PROVIDER_INVOKE_PATH=/layout-parsing
```

Notes:

- Keep OCR/Layout/VLM on separate ports in local debugging to reduce route ambiguity.
- Keep this capability sync for now and use async only when decision signals are consistently hit.

## Phase 3B Goal

Decide when to move from sync invocation to async job-mode.

## Decision Signals for Async

Move to async provider API when any of these is true:

- p95 latency > 15s for normal documents
- large PDFs regularly exceed request timeout
- GPU queueing makes sync retries noisy
- result artifacts (images/chunks/tables) exceed simple JSON envelope size
- sustained timeout rate > 5% in a rolling 24-hour window

## Recommended Async API Shape

- `POST /api/vlm/jobs`
- `GET /api/vlm/jobs/{job_id}`
- `GET /api/vlm/artifacts/{artifact_id}`

Job status fields:

- `queued`, `running`, `succeeded`, `failed`, `expired`
- `progress`
- `started_at`, `finished_at`
- `error` (structured)

## MyPrivateAgent Integration Plan

1. Keep `document.vlm.parse` for small sync calls.
2. `document.vlm.parse.async` is now available as placeholder job capability id:
   - `operation=submit`: submit job (`POST /api/vlm/jobs`)
   - `operation=status`: query job (`GET /api/vlm/jobs/{job_id}`)
3. Add polling helper in diagnostics panel for job status visibility.
4. Keep provider heartbeat and circuit-breaker behavior unchanged.

## Evaluation Matrix

- Accuracy: semantic extraction quality on contracts/invoices/forms
- Latency: p50/p95 per page and per document
- Stability: provider uptime and timeout profile
- Cost: GPU minutes and throughput under concurrent load
- Operability: error observability and artifact traceability

## Verification Suggestions

- Contract tests for sync envelope and error codes
- Integration test for async lifecycle transitions
- Frontend diagnostics test for job polling and result rendering
- A/B test: sync `document.vlm.parse` vs proposed `document.vlm.parse.async` on the same PDF set
