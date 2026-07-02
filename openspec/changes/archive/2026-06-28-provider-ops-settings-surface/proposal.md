## Why

`provider-ops-control-plane-v1` already exposes a read-only backend contract, but maintainers still need to inspect it from the product surface they already use for provider operations. The Settings page is the natural place because it already hosts provider configuration, onboarding, diagnostics, and failover observability.

Without a visible Settings surface, the provider ops control plane remains backend-only and is harder for maintainers to adopt in day-to-day review.

## What Changes

- Add a read-only Provider Ops card to the Settings provider tab.
- Load `/api/provider-ops` through the existing frontend API layer.
- Show compact posture summaries for credential, quota, rate limit, cost, SLA, and fallback.
- Keep the UI diagnostic-only and avoid configuration writes or execution actions.

## Non-Goals

- Do not add provider ops editing actions.
- Do not add runtime promotion or routing actions.
- Do not redesign the Settings page.
- Do not expose secrets or raw provider payloads.

## Impact

- Frontend: `SettingsView` and a dedicated provider ops component.
- Frontend tests: focused Settings/provider-ops rendering coverage.
- Docs/spec sync through this change only.
