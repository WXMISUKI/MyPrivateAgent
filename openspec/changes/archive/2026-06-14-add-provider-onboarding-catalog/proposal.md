## Why

MyPrivateAgent now has a generic `/api/service-providers` management surface, but the external projects we have already prepared still lack one clear onboarding catalog that tells maintainers how each provider is configured, which capabilities it supplies, how to verify readiness, and which runtime boundaries remain gated.

This change turns scattered provider setup knowledge into a small control-plane catalog so `unifiedKnowledgeRAG`, `unifiedTTSandASR`, PaddleOCR/OCR, Layout, and VLM-style providers can be connected and reviewed consistently.

## What Changes

- Add a provider onboarding catalog read model for known external provider families.
- Add read-only API endpoints that expose:
  - provider family identity and purpose
  - expected project/local URL
  - required environment variables
  - capability ids supplied to capability runtime
  - management endpoints and smoke/check commands
  - readiness checklist and promotion boundaries
- Include first catalog entries for:
  - `unifiedKnowledgeProvider`
  - `unifiedTTSandASR`
  - `paddleOCRProvider`
  - `paddleLayoutProvider`
  - `documentVlmProvider`
- Keep the catalog documentation-first and side-effect-free; it does not start services, mutate `.env`, create bindings, or invoke provider jobs.

收口对象：

- MyPrivateAgent-side onboarding catalog for already prepared external provider projects.
- Operator/developer-facing guidance that is machine-readable enough for UI and governance consumers.
- A compact readiness checklist that links provider onboarding to existing `/api/service-providers` and `/api/capabilities`.

非目标：

- Do not implement new provider runtime behavior.
- Do not modify external provider repositories.
- Do not start provider services or write `.env`.
- Do not enable default chat grounding, GraphRAG, source binding automation, voice default UX changes, OCR/VLM production promotion, queue workers, or provider marketplace workflows.

## Capabilities

### New Capabilities

- `provider-onboarding-catalog`: Defines the known external provider onboarding catalog, required configuration fields, capability mapping, readiness checklist, and side-effect-free API surface.

### Modified Capabilities

- `provider-service-consumption-contract`: Adds onboarding catalog cross-reference fields so provider management consumers can connect current provider readiness with setup guidance.

## Impact

- Backend:
  - New provider onboarding catalog service.
  - New read-only API routes, likely under `/api/provider-onboarding`.
  - Optional lightweight links from service provider entries to onboarding catalog ids.
- Tests:
  - Focused backend tests for catalog entries, readiness checklist shape, and API routes.
- Docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/guides/capability_runtime_registry.md`
- External systems:
  - No external provider repo changes.
  - No new runtime dependencies.
