## Why

`unifiedKnowledgeRAG` has reached the current explicit RAG provider closure line, but MyPrivateAgent still needs a clearer caller-owned service consumption contract so future external providers can be managed in the same way instead of through one-off scripts.

This change adds a small, provider-neutral management layer around external provider discovery, readiness, explicit capability invocation, and compact evidence packaging while preserving MyPrivateAgent as the Agent Runtime Control Plane.

## What Changes

- Add a provider service consumption contract that standardizes provider registry, manifest discovery, health/readiness normalization, explicit capability invocation, and caller-owned evidence packaging.
- Add a backend read model/service that can summarize external provider posture as `ready / review / blocked / unreachable / gated`.
- Add a small API surface for provider management and inspection, inspired by mature agent platform patterns:
  - provider registry/readiness list
  - provider detail/readiness
  - explicit capability invoke wrapper
  - evidence package preview
- Keep `unifiedKnowledgeRAG` as the first concrete provider instance through existing knowledge capability configuration.
- Keep provider consumption explicit and governed: no default chat retrieval injection, no GraphRAG execution, no source binding automation, no final answer policy promotion.

收口对象：

- MyPrivateAgent-side external provider consumption control contract.
- Provider-neutral management/readiness shape that future external projects can follow.
- Explicit, side-effect-free evidence for governance and integration debugging.

非目标：

- Do not optimize `unifiedKnowledgeRAG` retrieval strategy.
- Do not add query rewrite, rerank, hybrid retrieval, GraphRAG execution, or source binding automation.
- Do not enable default `/api/chat` RAG grounding.
- Do not move provider-owned indexing, model, parser, vector store, graph store, or job lifecycle concerns into MyPrivateAgent.

## Capabilities

### New Capabilities

- `provider-service-consumption-contract`: Defines the provider-neutral external service consumption model, readiness statuses, management endpoints, explicit invoke wrapper, and evidence package boundaries.

### Modified Capabilities

- `unified-knowledge-capability-runtime`: Knowledge provider health/readiness remains the first concrete input to the generic provider consumption model without changing existing knowledge capability requirements.

## Impact

- Backend:
  - `backend/capability_runtime/*`
  - new provider consumption read model/service and router if needed
  - focused tests under `tests/`
- APIs:
  - New read-only provider management endpoints under `/api/providers` or equivalent.
  - Optional explicit provider capability invoke endpoint that delegates to existing capability runtime.
- Docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/guides/capability_runtime_registry.md`
- External systems:
  - First concrete provider is `unifiedKnowledgeRAG` at `http://127.0.0.1:8020` when explicitly configured.
  - Future providers should expose manifest/health/capability-style metadata, but this change does not require a new provider implementation.
