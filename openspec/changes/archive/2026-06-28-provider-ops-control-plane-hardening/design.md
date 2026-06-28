## Context

Provider-facing control surfaces in MyPrivateAgent already separate configuration, onboarding, consumption, and failover. The next missing abstraction is an operations-oriented read model that explains whether a provider is safe to use from a governance perspective.

This is intentionally a control-plane concern. It does not own provider execution and does not replace the existing provider configuration or service-provider consumption contracts.

## Goals

- Provide a single read-only provider ops summary for each configured provider.
- Normalize operational posture into bounded, machine-readable fields.
- Keep the contract useful for Runtime Surface, Settings, and future governance checks.
- Preserve fail-closed semantics when evidence is missing or degraded.

## Decisions

### Decision 1: Provider ops is read-only

The provider ops contract only reports operational posture. It must not write provider configuration, adjust routing, or start external services.

### Decision 2: Provider ops is derived from existing control surfaces

The contract should be assembled from existing provider configuration, onboarding, service-provider consumption, and failover data. It should not require a separate provider execution subsystem.

### Decision 3: Operational posture is compact and bounded

The first version should expose a small set of stable posture fields:

- credential posture
- quota posture
- rate-limit posture
- cost posture
- SLA posture
- fallback posture

Each posture should include a status and a compact reason or next action when helpful.

### Decision 4: Missing evidence fails closed

If the system cannot determine a posture, it must report `unknown`, `review`, or a similarly bounded degraded state rather than inventing readiness.

### Decision 5: Secrets stay out of the contract

The contract may reference configuration presence or rotation state, but it must never expose API keys, tokens, or raw provider clients.

## Risks / Trade-offs

- The first version may be intentionally conservative and less expressive than a future provider ops dashboard.
- Because the contract is derived from multiple existing sources, normalization bugs could create confusing posture summaries.
- If the contract becomes too broad, it could overlap with provider onboarding or service-provider consumption. The scope must stay operational, not promotional.

## Verification Plan

- Add focused backend tests for a healthy provider ops posture.
- Add focused backend tests for missing credential or unknown posture.
- Add focused backend tests for degraded quota or fallback posture.
- Validate OpenSpec strictness before implementation is archived.
