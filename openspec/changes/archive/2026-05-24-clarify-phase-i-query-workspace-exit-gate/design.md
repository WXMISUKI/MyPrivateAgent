# Design

## Boundary

This change is a specification and documentation closure slice. It answers when implementation may resume, not how any new channel feature is implemented.

## Exit Gate Model

Phase I exits specification mode only when the following are simultaneously true:

- query workspace layer definitions are stable
- channel promotion gate has a recorded decision
- the next implementation target starts at the shallowest eligible layer
- the target has explicit non-goals preventing accidental promotion to deeper layers

If any of those facts are missing, the project stays in spec/architecture mode.

## Promotion Record

Channel promotion records should name:

- channel
- current layer
- target layer
- readiness evidence
- blockers
- decision
- next allowed action
- explicit non-goals

This keeps the decision reusable without requiring a new runtime endpoint in this slice.

## Verification

OpenSpec strict validation is sufficient because runtime code and API shape do not change.
