## Why

MyPrivateAgent already has domain-agent manifests, provider-neutral knowledge capabilities, and Runtime Surface knowledge registries, but agent-level grounding behavior is still only described in guide text. Before enabling default knowledge injection in `/api/chat`, the project needs a stable grounding policy contract that lets each agent declare citation requirements, ungrounded-answer behavior, fallback policy, and source ACL semantics.

## What Changes

- Add a new agent grounding policy capability that defines the structured policy fields used by domain agents.
- Extend domain-agent manifest discovery so `retrieval` / grounding fields can become governance-visible contract data.
- Expose grounding policy readiness through Runtime Surface read models before changing any default chat behavior.
- Document the allowed first implementation slice and the later promotion path toward chat retrieval injection.
- Non-goals:
  - Do not enable default `/api/chat` RAG injection in this change.
  - Do not add LlamaIndex, Neo4j, vector store, graph database, reranker, or embedding dependencies to MyPrivateAgent.
  - Do not implement PromptOps, MemoryOps, or multi-turn eval in this change.
  - Do not make the external knowledge provider a required startup dependency.

## Capabilities

### New Capabilities

- `agent-grounding-policy`: Defines agent-level knowledge grounding policy, readiness, fallback, and governance visibility.

### Modified Capabilities

- `domain-agent-asset-registry`: Domain agent manifests preserve normalized grounding policy fields from `retrieval` or future `grounding_policy` sections.
- `unified-knowledge-capability-runtime`: Knowledge capability health and source readiness can be referenced by grounding policy readiness without changing provider-neutral invocation contracts.

## Impact

- Affected backend contracts:
  - `backend/services/domain_agent_registry_service.py`
  - `backend/services/runtime_surface_profile_assembler.py`
  - Runtime Surface `domain_agent_registry`, and optionally a focused `grounding_policy_registry` read model.
- Affected docs:
  - `docs/guides/domain_agent_development_guide.md`
  - `docs/roadmap/provider_capability_gap_assessment_2026-06-03.md`
  - `docs/roadmap/next_phase_hardening.md`
- Affected tests:
  - focused backend tests around domain-agent manifest normalization and Runtime Surface profile assembly.
- Dependencies:
  - No new runtime dependency.
  - External provider readiness may improve policy readiness detail, but this change remains useful without the external provider being complete.
