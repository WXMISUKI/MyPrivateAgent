## Context

The Settings page already contains the provider-facing operational surfaces:

- ProviderConfigPanel
- ProviderOnboardingPanel
- CapabilityProviderDiagnosticsPanel
- Provider Failover observability

Provider Ops belongs beside those surfaces as another read-only operational card. To keep the change small, the first implementation should use a dedicated component and existing API access patterns.

## Decisions

### Decision 1: Provider Ops is a dedicated Settings component

The first implementation should live in its own component so the Settings view does not absorb additional rendering logic.

### Decision 2: The surface stays read-only

The UI should display posture and next action only. It should not add edit, retry, invoke, or promote actions.

### Decision 3: Status display remains compact

The first version should prioritize:

- summary counts
- per-provider overall status
- six posture fields
- reason / next action

### Decision 4: Errors fail closed in the UI

If provider ops data cannot be loaded, the UI should show an empty or degraded diagnostic state rather than hiding the section silently.

## Verification Plan

- Add focused component or Settings view tests for provider ops rendering.
- Verify the provider tab renders provider ops summary and per-provider posture fields.
- Keep the change isolated to frontend behavior and read-only API consumption.
