## Why

MyPrivateAgent can now call the local `company_profile` RAG path through an explicit API, but local development still requires developers to remember several separate smoke commands and interpret their outputs manually. For local usability, the project needs one doctor entrypoint that answers whether the local knowledge runtime path is usable and what to do next when it is not.

## What Changes

- Add a local knowledge runtime doctor mode to the existing doctor flow.
- Reuse the existing `company_profile` explicit API smoke service instead of duplicating provider calls.
- Support provider URL, API key, agent id, domain, query, top-k, and timeout options.
- Return a compact `go / review / blocked` report with check results, blockers, recovery action, and boundary details.
- Keep the doctor read-only and explicit: no provider startup, no default `/api/chat` retrieval injection, no source binding, no memory/audit/trace writes, no GraphRAG, no OCR, and no real LLM answer generation.

## Capabilities

### New Capabilities

- `local-knowledge-runtime-doctor`: Local developer-facing doctor contract for checking whether the explicit knowledge runtime path is usable.

### Modified Capabilities

- None.

## Impact

- Affected code:
  - `backend/services/doctor_runtime_service.py`
  - `backend/scripts/doctor.py`
  - optionally `backend/routers/health.py` for `/api/doctor` parity
- Affected tests:
  - focused tests for `go`, `blocked`, `review`, secret redaction, and boundary preservation
- Affected docs:
  - external RAG provider development guide
- No default chat, provider, memory, audit, trace, or GraphRAG behavior changes.
