# Design: PostgreSQL Advisory Lock Execution Seam

## Boundary

The execution seam is an internal Python component that accepts an optional executor callback. Without that callback, every operation returns compact blocked evidence and no SQL envelope is produced. With the callback, the seam builds a deterministic operation envelope and delegates execution to the caller-owned boundary.

The seam does not import database drivers, manage sessions, or infer production authorization. It is intentionally one-shot and testable.

## Operation Model

- `probe_once()` creates a safe probe envelope.
- `acquire_once(...)` requires `run_id`, `worker_id`, and `fencing_token` and derives a stable advisory lock key from `run_id`.
- `renew_once(...)` validates the same owner identity and emits a session-lock health envelope; it does not replace heartbeat renewal.
- `release_once(...)` requires owner identity and emits a release envelope.

Expected executor output is a mapping. The seam normalizes `ok`, `acquired`, `renewed`, and `released` booleans into compact evidence. Missing executor, missing owner identity, executor denial, and exceptions all fail closed.

## Contract Integration

`build_worker_ownership_postgres_advisory_lock_execution_seam_contract(...)` describes whether an executor is bound and whether one-shot operations are supported. The contract is embedded in PostgreSQL vendor lock probe evidence as `execution_seam`.

The worker ownership production gate reads this nested evidence and surfaces normalized fields in the `vendor_lock_semantics` section. This remains diagnostic evidence only; production lock allowment and default production ownership remain blocked unless future rollout and explicit enablement sections are complete.

## Safety Properties

- Constructing the seam starts no thread, timer, connection, or lock.
- Missing executor returns blocked evidence.
- SQL row lease/fencing is never promoted to vendor lock authority.
- Opt-in execution evidence does not enable production recovery or auto-claim.
