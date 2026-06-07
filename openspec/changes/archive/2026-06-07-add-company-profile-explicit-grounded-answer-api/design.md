## Context

MyPrivateAgent has already proven that it can call the running provider for `company_profile_2025_trial` through:

1. a local corpus trial,
2. a `company_profile` domain agent manifest,
3. a live grounded-answer trial that returns `go`.

The remaining gap is caller ergonomics. Business code should be able to invoke the capability through a stable HTTP API, but the default chat flow should remain untouched until a concrete business workflow needs it.

## Goals

- Provide an explicit HTTP API for caller-side company-profile/domain-agent grounded-answer trials.
- Keep the response compact enough for frontends and business code.
- Preserve full debug visibility through a nested trial payload.
- Reuse existing live trial behavior and manifest source scoping.

## Non-Goals

- Do not modify `/api/chat`.
- Do not automatically inject retrieved context into normal chat.
- Do not create source bindings.
- Do not write memory, audit, trace, or learning records.
- Do not execute GraphRAG, OCR, provider indexing, tools, or real LLM generation.
- Do not add a frontend UI in this slice.

## API Shape

```http
POST /api/domain-agents/{agent_id}/live-grounded-answer
```

Request:

```json
{
  "query": "公司主营业务是什么？",
  "domain": "company.profile",
  "provider_base_url": "http://127.0.0.1:8020",
  "top_k": 3,
  "timeout_seconds": 5
}
```

Response:

```json
{
  "ok": true,
  "status": "go",
  "reason_code": "live_grounded_answer_trial_ready",
  "answer_preview": "...",
  "citations": ["company_profile_2025_trial#chunk-4"],
  "documents": [],
  "boundary": {"default_chat_retrieval_injection": "disabled"},
  "trial": {}
}
```

## Decisions

### Add a response adapter instead of returning raw live trial reports

The raw live trial report is useful for debugging but too large for a normal caller contract. A small adapter keeps the API stable while preserving access to full details through `trial`.

### Keep the endpoint generic by agent id

The first target is `company_profile`, but the route should accept any manifest-backed domain agent. Source scoping remains controlled by the selected manifest.

### Do not require auth changes

The router already sits inside the existing backend API surface. This slice does not add new auth semantics; production access control can be introduced when a concrete business workflow needs it.

## Risks And Mitigations

- Provider unavailable: return `ok=false` with machine-readable `reason_code`.
- Response too large: expose compact top-level fields and keep full trial report nested for debugging.
- API key leakage: accept provider API key as input but never echo it in response or artifacts.
