## Context

The local RAG path now has two halves:

- Provider side: `company_profile_2025_trial` can be onboarded and registered as a local source.
- MyPrivateAgent side: `POST /api/domain-agents/company_profile/live-grounded-answer` exposes an explicit API for callers.

The new smoke should verify that these halves work together from the caller repository without requiring a browser, frontend, or MyPrivateAgent server process.

## Goals

- Provide one repeatable command for local explicit API validation.
- Produce a compact go/review/blocked artifact.
- Reuse the existing API route and response adapter.
- Preserve the same boundary guarantees as the explicit API.

## Non-Goals

- Do not connect retrieval to `/api/chat`.
- Do not create source-to-agent bindings.
- Do not write memory, audit, trace, or learning records.
- Do not start or manage the provider service.
- Do not parse PDFs, run OCR, or mutate provider data.
- Do not execute GraphRAG or real LLM answer generation.
- Do not add frontend UI.

## Approach

The smoke uses FastAPI `TestClient` with the existing `backend.routers.domain_agents.router`.

```text
company_profile_explicit_api_local_smoke.py
  -> TestClient(app).post("/api/domain-agents/company_profile/live-grounded-answer")
  -> existing DomainAgentLiveGroundedAnswerApiService
  -> provider /api/rag/retrieve
  -> compact smoke report
```

## Decision Rules

- `go`: HTTP 200, `ok=true`, `status=go`, at least one citation, at least one document, and boundary still disables default chat retrieval.
- `review`: HTTP 200 but response is not fully answerable while not transport-blocked.
- `blocked`: route fails, provider is unreachable, response contract is invalid, API key is echoed, or boundary is missing/unsafe.

## Output

The report includes:

- contract version and generated timestamp
- endpoint, agent id, domain, query, provider URL
- decision and reason code
- answer preview, citations, document count
- blockers, warnings, boundary
- compact response snapshot

Secrets supplied as provider API keys must never be written to JSON or Markdown output.
