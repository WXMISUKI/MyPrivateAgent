## Context

MyPrivateAgent already has HTTP capability definitions for `unifiedKnowledgeProvider`, including RAG retrieve and graph query invocation. The provider-side Phase 18 evidence says the minimal access gate is ready, but that is still provider-owned evidence. Phase 19 needs caller-owned proof from the MyPrivateAgent repository.

The implementation should be lightweight: a read-only trial outcome exporter that can be run locally against `http://127.0.0.1:8020` or another configured provider URL.

## Goals / Non-Goals

**Goals:**

- Prove MyPrivateAgent can access the provider through the minimal HTTP contract.
- Capture a compact outcome artifact for go/review/blocked decisions.
- Support optional provider API key headers for protected `/api/*` paths.
- Keep trial output deterministic and useful for follow-up debugging.

**Non-Goals:**

- Do not start or manage the provider service.
- Do not change default chat orchestration.
- Do not promote retrieval backends, GraphRAG, or answer composition.
- Do not create source-to-agent binding.
- Do not store secret values in artifacts.

## Decisions

### Decision: Add a dedicated trial outcome service

The trial logic will live in a small backend service module rather than inside the existing capability provider definitions. This keeps default runtime behavior unchanged and makes the trial runnable from tests or a CLI script.

### Decision: Use direct provider HTTP checks

The trial will call the provider discovery and source-binding endpoints directly, and use `/api/rag/retrieve` for the minimal retrieve path. This matches the real integration surface without requiring MyPrivateAgent chat or agent orchestration to be running.

### Decision: Classify outcomes conservatively

- `trial_passed`: all required checks pass.
- `trial_review`: provider is reachable but at least one check returns review/degraded/insufficient evidence that does not prove a hard protocol failure.
- `trial_blocked`: provider is unreachable, returns invalid JSON, required endpoint fails, or required response shape is missing.

## Risks / Trade-offs

- A passing trial does not prove final chat quality -> It only proves minimal provider access and evidence consumption readiness.
- A live run requires the provider service to be started separately -> The exporter will report `trial_blocked` with a clear failure reason if it is not reachable.
- Provider response schemas may evolve -> Tests cover the current minimal contract and fail closed on missing required fields.
