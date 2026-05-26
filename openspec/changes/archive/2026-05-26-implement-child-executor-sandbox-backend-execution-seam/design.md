# Design

## Current State

`child_executor_sandbox_worker_backend.py` already exposes:

- sandbox adapter readiness contract builder
- sandbox backend binding contract builder
- compact dispatch attempt envelope builder
- unsafe payload key detection
- dispatch attempt envelope validation

`ChildExecutorDispatcher` can invoke a callable backend adapter when dispatch is explicitly enabled and `dispatch_ready = true`.

## Proposed Design

Add a small opt-in execution seam in `child_executor_sandbox_worker_backend.py`:

- `SandboxChildExecutorBackend`
- constructor accepts `backend_id`, optional `executor`, and optional static policy fields
- construction has no side effects
- `dispatch(payload)` validates input and returns compact attempt evidence
- default executor is a deterministic local seam that returns refs, not unbounded child output
- caller can inject an executor for focused tests

The seam should classify outcomes:

- `completed`: payload valid and executor completes
- `blocked`: unsafe payload, missing required payload fields, or missing idempotency key
- `failed`: executor raises or returns malformed evidence

The seam should never perform parent merge, retry scheduling, or production authorization.

## Contract Fields

Runtime coverage should add execution seam evidence under `child_executor_sandbox_backend_coverage`:

- `execution_seam_supported`
- `execution_default_enabled`
- `execution_completed_status`
- `execution_blocked_status`
- `execution_missing_idempotency_status`
- `execution_handler_failure_status`
- `execution_invocation_count`
- `execution_parent_merge_performed`
- `execution_retry_scheduled`
- `execution_production_authorized`

## Fail-Closed Rules

- Unsafe payload keys block before executor invocation.
- Missing `child_run_id` or `idempotency_key` blocks before executor invocation.
- Executor exceptions produce compact failed evidence, not raw stack traces.
- Malformed executor result returns compact failed evidence.
- All default contract evidence continues to say dispatch is disabled unless an explicit dispatcher invokes the seam.

## Verification

Focused tests should prove:

- backend construction does not start work
- valid payload completes with compact envelope
- unsafe payload, missing idempotency, and missing child run id fail closed
- dispatcher can invoke the seam when explicitly enabled and binding evidence is ready
- runtime summary coverage remains explicit and default dispatch remains blocked
