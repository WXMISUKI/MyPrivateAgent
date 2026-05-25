# Design

## Approach

Introduce `WorkerOwnershipRenewalSupervisor` as an opt-in helper around the existing worker ownership store. Its only execution method is `renew_once(...)`, which validates required owner evidence and calls the store's existing `heartbeat(...)`.

## Contract Evidence

`build_worker_ownership_renewal_supervisor_contract(...)` will gain seam evidence:

- `renew_once_supported`
- `owner_identity_required`
- `ttl_interval_policy_ready`
- `lease_loss_fail_closed`

The production gate's `heartbeat_renewal_supervisor` section will surface these fields but remain blocked unless a true background supervisor is present and explicitly default-enabled.

## Failure Semantics

Missing store, missing owner identity, invalid lease/fencing evidence, expired lease, and stale fencing must return compact blocked evidence. These outcomes must not authorize recovery execution or imply production default enablement.
