## Why

MyPrivateAgent now exposes provider onboarding and live service-provider readiness contracts, but those read models are still API-only. Operators need a lightweight UI surface that makes external provider setup and current readiness visible without reading scattered docs or raw JSON.

This change adds a minimal read-only frontend surface for provider onboarding + live provider status so already prepared external projects can be connected and inspected consistently.

## What Changes

- Add a frontend API helper for:
  - `GET /api/provider-onboarding`
  - `GET /api/provider-onboarding/{onboarding_id}/readiness`
  - `GET /api/service-providers`
- Add a lightweight provider onboarding panel that displays:
  - known provider cards
  - required env var names and default URL
  - capability ids
  - configuration checklist
  - live service-provider status when available
  - management/evidence preview links as text paths
  - runtime boundaries such as default chat grounding, GraphRAG, source binding, and provider startup
- Place the panel in the existing settings/capability diagnostics area rather than creating a marketplace.
- Keep the UI read-only.

收口对象：

- Frontend consumption shell for provider onboarding and service-provider readiness.
- A simple operator-facing view that helps external provider projects connect smoothly to MyPrivateAgent.

非目标：

- Do not write `.env` or provider configuration from the UI.
- Do not start external provider services.
- Do not invoke RAG, OCR, VLM, ASR/TTS, GraphRAG, source binding, or heavy provider jobs.
- Do not create a dynamic provider marketplace.
- Do not redesign settings or governance pages broadly.

## Capabilities

### New Capabilities

- `provider-onboarding-ui-surface`: Defines the read-only frontend surface for provider onboarding catalog and live service-provider readiness consumption.

### Modified Capabilities

- `provider-onboarding-catalog`: Adds UI consumption expectations for list/readiness fields.
- `provider-service-consumption-contract`: Adds UI consumption expectations for live provider status and onboarding cross-links.

## Impact

- Frontend:
  - API helper under `frontend-vue/src/api/` or existing API facade.
  - New Vue component for provider onboarding/status.
  - Settings/capability diagnostics integration.
  - Focused component/API tests.
- Backend:
  - No new backend behavior expected.
- Docs/specs:
  - `docs/guides/capability_runtime_registry.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
