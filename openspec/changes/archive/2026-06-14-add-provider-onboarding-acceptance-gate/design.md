## Context

The provider integration path currently has three stable layers:

- Static setup guidance: `provider-onboarding-catalog-v1`
- Live management/readiness: `provider-service-consumption-v1`
- Operator visibility: `provider-onboarding-ui-surface`

The next step is not more provider internals. It is a reusable acceptance gate that can prove a known external provider is safe for explicit MyPrivateAgent consumption without invoking heavy workloads or mutating runtime state.

## Goals / Non-Goals

**Goals:**

- Produce deterministic acceptance evidence for a known provider.
- Support lookup by `onboarding_id` and `provider_id`.
- Decide whether a provider is `accepted`, `review`, or `blocked` for explicit managed-provider consumption.
- Keep evidence compact and free of secrets/raw provider data.
- Provide a CLI-friendly script for local operator and CI use.

**Non-Goals:**

- Do not add or change backend API routes in this slice.
- Do not call provider capability invoke/test endpoints.
- Do not start or stop provider processes.
- Do not write configuration or `.env`.
- Do not treat acceptance as default runtime promotion.

## Decisions

1. **Implement a service plus script, not a new API route.**
   The acceptance gate is initially an operator/CI artifact. A route can be added later if governance UI needs it. This keeps the blast radius small and avoids expanding public API surface prematurely.

2. **Build evidence from existing contracts.**
   The gate consumes `ProviderOnboardingCatalogService` and `ProviderConsumptionService` instead of duplicating provider rules. This keeps onboarding, live readiness, and acceptance in sync.

3. **Use conservative decisions.**
   `accepted` requires configured onboarding, registered service provider, live provider status `ready` or `review`, and expected capability ownership. Missing configuration, missing live provider, blocked/unreachable/disabled/unconfigured status, or capability mismatch blocks acceptance.

4. **Keep execution boundary explicit.**
   The acceptance evidence includes a boundary block that states default chat grounding, GraphRAG, source binding automation, provider startup, and final answer policy remain not promoted.

## Risks / Trade-offs

- [Risk] Acceptance can be mistaken for production promotion. -> Mitigation: evidence explicitly says it only allows explicit managed-provider consumption.
- [Risk] Some providers may be intentionally unregistered in local development. -> Mitigation: missing live provider is `blocked` with a clear reason rather than a hard exception.
- [Risk] Script output could accidentally include unsafe payloads if source contracts change. -> Mitigation: service constructs a whitelist-based evidence package.
