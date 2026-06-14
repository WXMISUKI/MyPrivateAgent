## Why

MyPrivateAgent now has the external provider building blocks in place: onboarding catalog, service-provider management contract, and a read-only settings UI. The remaining gap is a repeatable acceptance gate that tells maintainers when an external project is actually ready to be consumed by MyPrivateAgent as a managed provider.

Without this gate, future providers can still rely on scattered docs, manual interpretation, or one-off smoke scripts. This change adds a deterministic, read-only acceptance package so `unifiedKnowledgeRAG`, voice, OCR, layout, VLM, and later providers can be validated against the same contract before broader use.

## What Changes

- Add a provider onboarding acceptance gate contract.
- Add a lightweight backend acceptance service/script that:
  - accepts an `onboarding_id` or `provider_id`
  - reads provider onboarding detail
  - reads onboarding readiness checklist
  - reads service-provider management status when registered
  - emits compact JSON evidence and a machine-readable decision
- Add focused tests covering:
  - configured/registered provider acceptance
  - unconfigured onboarding fail-closed/review behavior
  - unknown provider failure
  - evidence excludes secrets, raw provider payloads, generated answers, and executable handles
- Update docs/runbook so future external projects know how to prove readiness.

Non-goals:

- Do not invoke provider capabilities.
- Do not run OCR, VLM, RAG, ASR/TTS, GraphRAG, source binding, or chat workflows.
- Do not write `.env`, start provider services, or mutate runtime configuration.
- Do not promote default `/api/chat` grounding or final answer policy.
- Do not introduce a provider marketplace.

## Capabilities

### New Capabilities

- `provider-onboarding-acceptance-gate`: Defines the deterministic read-only acceptance evidence and decision model for external provider onboarding.

### Modified Capabilities

- `provider-onboarding-catalog`: Adds acceptance-gate consumption expectations for onboarding detail/readiness.
- `provider-service-consumption-contract`: Adds acceptance-gate consumption expectations for live provider status and explicit-use boundaries.

## Impact

- Backend:
  - New service/script under backend capability runtime or scripts.
  - Focused unit tests.
- Docs/specs:
  - New canonical spec for provider acceptance gate.
  - Updates to provider onboarding/service provider specs.
  - Updates to capability runtime guide, runtime contracts, and next-phase roadmap.
