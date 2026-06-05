## Context

Domain agents can already declare `capabilities.rag_sources` and `capabilities.graph_sources`, and Runtime Surface exposes read-only knowledge registries derived from manifests. The guide also recommends a `retrieval` block with fields such as `require_citations` and `fallback_policy`, but those fields are not yet normalized, validated, or surfaced as a stable contract.

The external RAG / GraphRAG provider is still under development, so this change must remain useful without relying on a production-ready provider. The first implementation should make grounding policy visible and testable, while keeping `/api/chat` behavior unchanged.

## Goals / Non-Goals

**Goals:**

- Define a stable agent grounding policy contract for domain-agent manifests.
- Normalize policy fields such as `require_citations`, `allow_ungrounded`, `must_use_knowledge_for_domains`, `fallback_policy`, and `source_acl_mode`.
- Expose policy readiness through Runtime Surface, preferably as part of the domain-agent read model and/or a focused grounding registry.
- Preserve fail-open startup behavior when the external knowledge provider is absent or degraded.
- Document the later promotion path for chat retrieval injection.

**Non-Goals:**

- No default `/api/chat` retrieval injection.
- No provider-side RAG, GraphRAG, embedding, vector store, reranker, parser, or graph database implementation.
- No PromptOps, MemoryOps, or multi-turn eval implementation.
- No UI-heavy prompt studio or knowledge management console.

## Decisions

1. **Grounding policy lives with domain-agent assets.**
   - Decision: The first contract reads policy from `agent.yaml`, under `grounding_policy` first and legacy-compatible `retrieval` second.
   - Alternative considered: Put policy only in prompts or external provider catalog.
   - Rationale: Prompts are not reliably machine-readable, and provider catalogs own source readiness rather than business answer behavior.

2. **Runtime Surface exposes policy before chat uses it.**
   - Decision: The first implementation surfaces normalized policy/readiness but does not alter model input assembly.
   - Alternative considered: Immediately inject RAG into `/api/chat` when policy requires citations.
   - Rationale: Default retrieval affects answer behavior and needs a later eval gate plus provider readiness.

3. **Readiness is descriptive, not blocking.**
   - Decision: Missing policy fields, unavailable provider catalog, or unknown source readiness should produce machine-readable `degraded` or `unknown` readiness without blocking application startup.
   - Alternative considered: Fail startup or hide the agent.
   - Rationale: MyPrivateAgent is the control plane; provider data-plane availability should be visible, not a hard dependency.

4. **Allowed values stay small in the first slice.**
   - Decision: Start with bounded enums for `fallback_policy` and `source_acl_mode`.
   - Alternative considered: Free-form strings only.
   - Rationale: Governance UI, tests, and future eval gates need stable values.

## Risks / Trade-offs

- [Risk] Grounding policy is exposed but not enforced in chat yet. -> Mitigation: readiness output MUST include `enforcement = visibility_only` or equivalent wording until a later promotion change.
- [Risk] Existing `retrieval` guide fields drift from future `grounding_policy`. -> Mitigation: support both shapes initially, document `grounding_policy` as the durable name, and keep `retrieval` as compatibility input.
- [Risk] Policy fields become too broad. -> Mitigation: restrict the first implementation to manifest normalization, Runtime Surface visibility, and focused tests.

## Migration Plan

1. Add OpenSpec requirements for the new grounding policy contract.
2. Normalize manifest policy fields in `DomainAgentRegistryService`.
3. Expose normalized policy/readiness through Runtime Surface without changing `/api/chat`.
4. Update the domain-agent guide with the durable `grounding_policy` example.
5. Add focused tests for manifest normalization and Runtime Surface profile assembly.
6. Archive the change after validation.

Rollback: remove the normalized policy output and guide section. Existing `capabilities.rag_sources`, `capabilities.graph_sources`, and chat behavior remain unchanged.

## Open Questions

- Should the later enforcement change live in `/api/chat` input assembly, a dedicated grounding policy service, or the query control plane?
- Should `must_use_knowledge_for_domains` initially be a list of strings, or should it become a structured taxonomy owned by domain-agent assets?
