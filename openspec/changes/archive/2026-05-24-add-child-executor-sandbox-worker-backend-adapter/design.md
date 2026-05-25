# Design

## Boundary

This change defines the contract that future sandbox worker backend implementations must satisfy. It does not implement the worker, queue, process isolation, or runtime execution path.

## Adapter Contract

A sandbox worker backend adapter must expose a machine-readable contract before it can be registered as dispatch-ready:

- `backend_id`
- `adapter_kind`
- `contract_version`
- `sandbox_mode`
- `execution_mode`
- `input_contract`
- `output_contract`
- `resource_limits`
- `isolation_guards`
- `audit_hooks`
- `idempotency`
- `failure_modes`

The adapter contract is distinct from dispatch attempt output. The contract answers "can this backend be selected"; the attempt output answers "what happened when opt-in dispatch invoked it."

## Dispatch Attempt Envelope

When the dispatcher invokes an enabled sandbox adapter, the adapter result must be a compact object:

- `attempt_id`
- `backend_id`
- `child_run_id`
- `status`
- `will_dispatch`
- `dispatch_started_at`
- `dispatch_finished_at`
- `sandbox_ref`
- `output_ref`
- `audit_ref`
- `error_code`
- `retryable`

It must not include executable callables, provider clients, open streams, raw process handles, or unbounded tool output.

## Sandbox Guards

The first production adapter should be explicitly opt-in and bounded. Required guard categories are:

- process or worker isolation evidence
- resource limits
- timeout policy
- environment allowlist
- filesystem/workspace boundary
- network policy
- audit recording
- idempotency key

If any required guard is missing, registry and dispatch contracts fail closed.

## Integration Points

- Backend registry can list a sandbox backend, but `dispatch_ready=true` requires adapter contract readiness and sandbox guard evidence.
- Dispatch contract can become ready only when promotion gate, execution prerequisites, backend registry, and sandbox backend evidence are all ready.
- Dispatcher invokes adapters only when explicitly enabled and dispatch contract is ready.

## Failure Mode

Malformed adapter contracts, malformed attempt output, adapter exceptions, missing audit hooks, missing idempotency, or missing sandbox guard evidence all fail closed and set `will_dispatch=false`.
