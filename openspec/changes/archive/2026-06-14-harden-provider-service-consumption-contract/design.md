## Context

MyPrivateAgent already has a `capability_runtime` for voice, document, and knowledge capabilities. `unifiedKnowledgeRAG` is now usable as an explicit external RAG provider through `knowledge.rag.retrieve`, and its readiness is already surfaced through compact `governance_readiness`.

The remaining gap is management consistency. External providers are currently discoverable through capability-specific paths and scripts, but future providers need a simple control-plane shape that answers the same questions every time:

- Is the provider configured and reachable?
- Which capabilities does it expose?
- Is this capability safe to invoke explicitly?
- What is gated and why?
- What evidence can governance/debugging consumers read without copying raw provider payloads?

Mature agent platforms commonly separate provider registry, manifest discovery, health/readiness, capability invocation, and audit/evidence views. This design adopts that pattern in a lightweight way while keeping MyPrivateAgent in control of governance and keeping execution/data lifecycle inside each provider.

## Goals / Non-Goals

**Goals:**

- Add a provider-neutral read model for external service consumption.
- Expose a small management API for provider list/detail/readiness, explicit capability invocation, and evidence package preview.
- Reuse existing `capability_runtime` provider implementations instead of adding another provider execution stack.
- Use `unifiedKnowledgeRAG` as the first provider instance.
- Keep returned provider evidence compact and safe for governance surfaces.

**Non-Goals:**

- Do not enable default `/api/chat` retrieval injection.
- Do not execute GraphRAG or treat GraphRAG schema presence as execution readiness.
- Do not create source-to-agent bindings, approvals, memory, or audit records.
- Do not import provider-owned dependencies such as LlamaIndex, vector stores, graph stores, OCR engines, or model SDKs.
- Do not add a production provider marketplace, queue, scheduler, or retry worker.

## Decisions

1. **Add a provider consumption service above capability runtime.**

   The new service reads existing capability runtime registry, heartbeat, and health information, then normalizes provider posture. It does not replace `CapabilityRuntimeService` or provider classes.

   Alternative considered: adding provider management fields directly to each provider class. That would make the first slice smaller but would duplicate readiness mapping across knowledge, voice, OCR, VLM, and future providers.

2. **Use a compact provider read model.**

   Provider entries expose `provider_id`, `kind`, `transport`, `base_url`, `configured`, `enabled`, `overall_status`, `capabilities`, `readiness`, `gates`, `warnings`, and `boundaries`.

   The status vocabulary is intentionally small: `ready / review / blocked / unreachable / gated / disabled / unconfigured / unknown`.

   Alternative considered: copying provider `/health` or `/manifest` payloads directly. That would be easier but would leak provider-specific fields, large payloads, and possibly secret-adjacent diagnostics into governance surfaces.

3. **Keep explicit invocation delegated to capability runtime.**

   The provider API accepts `provider_id`, `capability_id`, and a payload. It verifies that the provider owns the capability and then delegates to `CapabilityRuntimeService.invoke(...)`.

   Alternative considered: calling provider HTTP endpoints directly from the new service. That would create a second execution path and weaken existing capability contracts.

4. **Evidence package is preview-only and caller-owned.**

   The evidence preview summarizes provider readiness, available capabilities, gated capabilities, invocation boundary, and recommended next action. It does not create durable audit records or source bindings.

   Alternative considered: writing governance timeline records in this slice. That is useful later, but this first contract should stay read-only and low-risk.

5. **`unifiedKnowledgeRAG` remains a concrete provider instance, not a special platform dependency.**

   Its `governance_readiness` fields seed the generic readiness block, but the generic contract must also work for voice/OCR/VLM-style providers that do not expose RAG-specific fields.

## Risks / Trade-offs

- [Risk] A generic provider API may duplicate capability runtime concepts. -> Mitigation: treat it as a management/readiness read model and delegate all execution to existing capability runtime.
- [Risk] Consumers may treat `ready` as production promotion. -> Mitigation: every evidence package includes explicit boundaries for default chat, GraphRAG, source binding, and final answer policy.
- [Risk] Provider-specific health payloads may drift. -> Mitigation: normalize only compact known fields and preserve unknown provider details out of the management contract.
- [Risk] Future providers may not expose manifest endpoints. -> Mitigation: the first contract allows `manifest.status = unknown` while still reporting configured capability metadata from MyPrivateAgent.

## Migration Plan

1. Add the provider consumption service and router with disabled/unconfigured behavior.
2. Wire the knowledge provider instance from existing environment configuration.
3. Add focused tests for disabled, ready, unreachable, explicit invocation, and evidence preview behavior.
4. Document the contract and archive the OpenSpec change.
