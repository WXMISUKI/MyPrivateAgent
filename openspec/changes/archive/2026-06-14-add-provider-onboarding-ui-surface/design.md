## Context

MyPrivateAgent already exposes two backend read models for external provider integration:

- `/api/provider-onboarding` answers how known external projects should be connected.
- `/api/service-providers` answers whether currently registered external providers are usable.

The current gap is operational visibility. Maintainers must still read docs or raw API JSON to connect `unifiedKnowledgeRAG`, voice, OCR, layout, and VLM providers. The next UI slice should make the existing contracts visible without turning settings into a provider marketplace or configuration writer.

## Goals / Non-Goals

**Goals:**

- Add a read-only settings panel that consumes provider onboarding and live service-provider readiness.
- Show provider identity, env var names, default URLs, capability ids, readiness checks, live status, management paths, and runtime boundaries.
- Keep the panel side-effect-free: refresh-only, no provider invocation, no service startup, no `.env` writes.
- Reuse the existing settings "模型与 Provider" area and API facade patterns.

**Non-Goals:**

- Do not change backend provider contracts.
- Do not enable default `/api/chat` RAG grounding, GraphRAG execution, source binding automation, or final answer policy changes.
- Do not submit OCR/VLM/RAG/ASR/TTS jobs from this panel.
- Do not create dynamic provider installation, marketplace, or configuration editing.

## Decisions

1. **Use a separate `ProviderOnboardingPanel.vue`.**
   Rationale: `ProviderConfigPanel` edits model provider settings and `CapabilityProviderDiagnosticsPanel` can execute active diagnostics. A separate read-only panel keeps onboarding guidance distinct from mutation and explicit testing.

2. **Consume backend read models directly.**
   Rationale: The frontend should not derive provider status from capability ids locally. It will join onboarding entries and service-provider entries by `provider_id`, while keeping backend fields as the source of truth.

3. **Fetch readiness per onboarding entry after catalog load.**
   Rationale: The catalog list is compact but readiness checks are the operator-facing checklist. Fetching per entry keeps backend contracts unchanged and avoids adding a bulk endpoint before it is needed.

4. **Show paths as text, not action buttons.**
   Rationale: The current phase is visibility and controlled handoff. Text paths are enough to expose management/evidence endpoints without inviting heavy provider calls.

## Risks / Trade-offs

- [Risk] Multiple requests can make the panel look noisy if the backend is unavailable. -> Mitigation: fail open with a compact error and keep the rest of settings usable.
- [Risk] Users may interpret `ready` as production promotion. -> Mitigation: always show boundaries beside live status and keep labels focused on explicit provider use.
- [Risk] The UI may duplicate docs. -> Mitigation: show only operational fields and doc paths, not long setup prose.
