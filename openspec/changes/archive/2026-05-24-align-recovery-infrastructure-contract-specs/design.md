# Design

## Boundary

This change is a spec alignment slice. Runtime behavior already normalizes and guards the fields; the work is to make canonical specs describe that fact precisely.

## Current Implementation Facts

- Health Router degraded traces normalize `recovery_retry_scheduler_coverage`, `durable_recovery_loader_coverage`, and `child_executor_dispatcher_coverage` into `payload.runtime_contract_summary`.
- Trace detail already emits compact labels for `recovery_retry_scheduler`, `durable_loader`, and `child_executor_dispatcher`.
- Runtime Contract Snapshot stable fields already include nested guard paths for retry scheduler, durable loader, and child executor dispatcher smoke fields.

## Spec Updates

- `runtime-contract-trace-summary-coverage` will name the full supported coverage set rather than the older partial set.
- `runtime-contract-summary-nested-snapshot` will add explicit scenarios for missing scheduler, durable loader, and dispatcher coverage objects and smoke flags.

## Failure Mode

Legacy or malformed summaries continue to fail closed through existing implementation. This change does not alter fallback values or add new runtime paths.
