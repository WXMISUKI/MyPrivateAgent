## Context

Runtime Surface is the project’s contract-oriented governance entrypoint. If a control-plane read model is mature enough to be reviewed by maintainers, it should usually be available there.

Provider Ops already exists as:

- backend read-only endpoint
- Settings provider tab card

The next smallest safe step is to expose the same posture in Runtime Surface without adding any action semantics.

## Decisions

### Decision 1: Runtime Surface carries the compact provider ops contract

The runtime profile should include a compact `provider_ops` object rather than forcing the frontend to make another ad hoc API call.

### Decision 2: Runtime Surface rendering stays compact

The panel should show:

- summary counts
- provider overall status
- compact posture fields

This keeps Runtime Surface aligned with its contract-inspection role.

### Decision 3: Governance visibility does not imply timeline events

This change only adds visibility to Runtime Surface. It does not create governance timeline entries, replay state, or alert routing.

## Verification Plan

- Add focused backend assertions that `provider_ops` appears in runtime profile.
- Add focused RuntimeSurfacePanel test coverage for provider ops rendering.
- Validate the change with strict OpenSpec and focused tests only.
