## Why

MyPrivateAgent already has provider configuration, onboarding, service-provider consumption, and failover observability contracts. What is still missing is a unified provider ops control plane that explains whether a provider is operationally safe from a governance perspective.

Without this layer, teams can see that a provider exists and whether it is reachable, but they still cannot answer the operational questions that usually block production use:

- Are credentials configured and rotated?
- Is the provider within quota or rate limit budget?
- Is the current cost posture acceptable?
- Is the provider meeting its SLA posture?
- If the provider degrades, what fallback posture is active?

This change defines a read-only provider ops contract so the platform can expose those facts without changing provider execution behavior.

## What Changes

- Define a compact provider ops read model for configured external providers.
- Expose credential, quota, cost, SLA, rate-limit, and fallback posture as governance-visible data.
- Keep the contract read-only and fail-closed for missing or unknown operational evidence.
- Allow Runtime Surface and settings consumers to inspect provider ops posture without mutating provider configuration or routing.
- Keep secrets, raw payloads, and execution promotion out of the contract.

## Non-Goals

- Do not add a provider marketplace.
- Do not auto-route traffic or promote fallback behavior.
- Do not store or expose API keys, tokens, or raw provider responses.
- Do not change `/api/chat`, provider execution, or provider startup behavior.
- Do not build billing, chargeback, or tenant management in this slice.

## Impact

- Backend: provider ops read model service and read endpoint.
- Runtime Surface: compact `provider_ops` summary for governance consumers.
- Tests: focused backend tests for configured, missing, and degraded provider ops posture.
- Docs: update architecture and roadmap notes to reflect the new provider ops control plane.
