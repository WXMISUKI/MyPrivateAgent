# Design

## Approach

Extend `WorkerOwnershipRenewalSupervisor` with explicit lifecycle methods:

- `start(run_id, worker_id, lease_id, fencing_token)`
- `stop()`
- `status()`

`start(...)` performs one immediate `renew_once(...)` before creating a daemon renewal loop. If that first renewal fails, the supervisor remains inactive and reports blocked evidence. `stop()` sets a stop event and joins the loop briefly.

## Contract Evidence

The renewal supervisor contract will expose lifecycle posture:

- `controlled_lifecycle_supported`
- `starts_by_default`
- `active`
- `last_renewal_status`
- `stop_supported`
- `failure_fail_closed`

Production gate evidence will surface the same fields but keep the `heartbeat_renewal_supervisor` section blocked unless a production background supervisor is explicitly default-enabled and rollout is confirmed.

## Safety

The lifecycle is opt-in and local to the constructed supervisor instance. It does not register with app startup, does not auto-claim recovery ownership, and treats renewal failure as blocked state.
