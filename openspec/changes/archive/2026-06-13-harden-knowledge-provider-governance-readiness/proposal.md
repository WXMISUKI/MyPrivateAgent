## Why

`unifiedKnowledgeRAG` has reached the local explicit-use closure line as a lightweight external RAG provider. MyPrivateAgent now needs a caller-owned governance readiness surface that can explain provider configuration, health, RAG readiness, source catalog posture, and GraphRAG gating without reopening provider-side optimization or changing default chat behavior.

## What Changes

- Add a read-only Knowledge Provider governance readiness contract in MyPrivateAgent.
- Surface whether the external provider is configured/enabled, reachable, RAG-ready, source-catalog-ready/degraded, and graph execution separately gated.
- Keep readiness fail-open for the main app and ordinary chat.
- Preserve explicit caller boundaries: no default `/api/chat` retrieval injection, no source binding automation, no GraphRAG execution, no final answer policy change.
- Non-goals:
  - Do not modify `D:\AI\AIcode\unifiedKnowledgeRAG`.
  - Do not add query rewrite, rerank, hybrid retrieval, GraphRAG execution, or source binding automation.
  - Do not create a production deployment gate.
  - Do not change prompt, memory, audit, approval, or answer composition behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `unified-knowledge-capability-runtime`: add a caller-owned governance readiness read model for the external knowledge provider after local explicit-use closure.

## Impact

- Affected backend:
  - `backend/capability_runtime/providers/knowledge_http_provider.py`
  - `backend/capability_runtime/service.py` or adjacent runtime surface/capability helpers
  - capability provider heartbeat/readiness tests
- Affected docs/specs:
  - `openspec/specs/unified-knowledge-capability-runtime/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/guides/capability_runtime_registry.md`
- Verification:
  - Focused capability provider/runtime tests.
  - `openspec validate --all --strict`.
