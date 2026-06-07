## Why

MyPrivateAgent now exposes an explicit `company_profile` grounded-answer API, and the provider can onboard the local company-profile source. The remaining local usability gap is a repeatable caller-side smoke command that verifies the full explicit API path after the provider is started.

## What Changes

- Add a caller-side local smoke exporter for `POST /api/domain-agents/company_profile/live-grounded-answer`.
- Default to `agent_id=company_profile`, `domain=company.profile`, and query `公司主营业务是什么？`.
- Call the existing FastAPI router through `TestClient`, so MyPrivateAgent does not need a separately running backend process.
- Require only the external provider URL to be reachable.
- Export JSON and Markdown artifacts under `docs/integration/company-profile-explicit-api-local-smoke/`.
- Keep the smoke explicit and side-effect-free: no default `/api/chat` retrieval injection, no source binding, no memory/audit/trace writes, no OCR, no GraphRAG, no real LLM answer generation, and no provider startup.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-agent-live-grounded-answer-trial`: Add a local caller-side smoke exporter for the explicit live grounded-answer API.

## Impact

- Affected code:
  - new smoke service or script under `backend/` for local explicit API verification
- Affected tests:
  - focused tests for go, blocked, API key redaction, and boundary preservation
- Affected docs:
  - external RAG provider guide local smoke command
- No default runtime behavior changes.
