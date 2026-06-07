## Context

MyPrivateAgent already has provider-neutral knowledge capability registration, repo-side provider trial outcome export, and domain-agent live grounded-answer trial. The missing slice is narrower: use the real provider-local company corpus source that has already passed provider-side live HTTP smoke.

This change should not reopen the provider readiness chain. It should produce a MyPrivateAgent-owned trial result over the exact local source and questions the provider already accepted.

## Goals / Non-Goals

**Goals:**

- Verify MyPrivateAgent can call the live provider for `company_profile_2025_trial`.
- Validate source visibility, manifest availability, retrieve results, answer results, citation allowlists, and negative-control behavior.
- Produce a compact `go` / `review` / `blocked` artifact.
- Keep the code testable with `httpx.MockTransport` and runnable against `http://127.0.0.1:8020`.

**Non-Goals:**

- Do not start or manage `unifiedKnowledgeRAG`.
- Do not mutate domain-agent manifests or create source-to-agent binding.
- Do not enable default `/api/chat` retrieval injection.
- Do not call LLMs, create final user-facing answers, write audit/memory records, or promote grounding.
- Do not promote Qdrant/BGE/GraphRAG, parse PDFs, or start OCR services.

## Decisions

### Decision: Add a dedicated corpus trial service

The existing repo-side provider trial checks generic access and source-binding review. This change needs case-level corpus behavior, including answer citations and a negative-control query. A dedicated service keeps the generic trial stable and avoids overloading the earlier Phase 19 artifact.

### Decision: Use direct provider HTTP endpoints

The trial calls `/api/rag/*` endpoints directly rather than going through default chat or domain-agent answer composition. This is the smallest caller-shaped verification of the provider data plane and avoids prematurely promoting grounded-answer behavior.

### Decision: Fail closed on citation mismatch

Answer citations must be a subset of the retrieve response citations for the same query. Citation drift is treated as `blocked` because MyPrivateAgent cannot safely ground final answers when provider answer citations exceed retrieved evidence.

## Risks / Trade-offs

- Provider service not running -> report `blocked` with a clear unreachable reason.
- Provider API key enabled -> accept optional API key headers while redacting secret values from artifacts.
- Passing corpus trial does not prove final answer UX -> this is a data-plane/caller-contract trial only; final answer policy stays separately gated.
