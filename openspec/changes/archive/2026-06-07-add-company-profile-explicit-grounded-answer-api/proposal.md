## Why

The company-profile provider source and domain-agent live trial now both return `go`. The next useful step is to expose a stable, explicit MyPrivateAgent API that callers can use for local business trials without depending on a command-line script or changing the default chat path.

## What Changes

- Add an explicit domain-agent live grounded-answer API endpoint.
- Reuse the existing live provider-backed grounded-answer trial service.
- Return a compact caller-facing response with status, reason, answer preview, citations, retrieved documents, and boundary.
- Keep the full trial report available under a nested `trial` field for debugging.
- Support optional provider base URL, API key, top-k, and timeout parameters.
- Keep the endpoint opt-in and side-effect-free: no default `/api/chat` retrieval injection, no source-to-agent binding creation, no audit or memory writes, no GraphRAG, no provider mutation, and no real LLM answer generation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-agent-live-grounded-answer-trial`: Add a caller-facing explicit API surface for running a live grounded-answer trial.

## Impact

- Affected code:
  - `backend/routers/domain_agents.py`
  - new lightweight API response adapter under `backend/services/`
- Affected tests:
  - focused router/service tests with mocked provider transport
- Affected docs:
  - external RAG provider guide API example
- No default runtime behavior changes.
