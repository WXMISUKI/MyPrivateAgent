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

## Phase 3B Goal

Decide when to move from sync invocation to async job-mode.

## Decision Signals for Async

Move to async provider API when any of these is true:

- p95 latency > 15s for normal documents
- large PDFs regularly exceed request timeout
- GPU queueing makes sync retries noisy
- result artifacts (images/chunks/tables) exceed simple JSON envelope size

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
2. Add `document.vlm.parse.async` as a separate capability id for jobs.
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
