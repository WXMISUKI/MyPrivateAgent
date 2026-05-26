# Design

## Current State

`build_child_executor_dispatch_contract(...)` already composes promotion gate, execution prerequisites, backend registry evidence, and sandbox backend binding evidence. It can technically report ready if these inputs are ready, but the project lacks a dedicated opt-in ready sandbox sample and stable gate coverage proving this path.

`SandboxChildExecutorBackend` provides an explicit opt-in execution seam, but its support evidence is not yet part of dispatch contract readiness.

## Proposed Design

Add optional dispatch-builder inputs:

- `payload`
- `sandbox_execution_seam`
- `explicit_sandbox_backend_binding`

The builder will continue to be side-effect-free. It will inspect evidence only:

- sandbox backend registry entry is dispatch-ready
- sandbox backend binding is ready
- execution seam evidence reports `supported = true`
- payload includes `child_run_id` and `idempotency_key`
- payload does not include unsafe sandbox runtime objects

When all existing and new requirements are ready:

- `overall_status = ready`
- `dispatch_ready = true`
- `will_dispatch = false`
- `relationship_seam_preserved = true`
- `child_executor_dispatch_attempt_handoff.ready = true`

When evidence is missing:

- keep `overall_status = blocked`
- keep `dispatch_ready = false`
- include stable blockers such as `sandbox_execution_seam_supported`, `sandbox_payload_idempotency_ready`, or `sandbox_payload_unsafe`

## Contract Fields

Add stable evidence under `child_executor_dispatch_contract`:

- `sandbox_execution_seam_supported`
- `sandbox_payload_idempotency_ready`
- `sandbox_payload_child_run_ready`
- `sandbox_payload_unsafe_keys`
- `sandbox_dispatch_ready_opt_in`

Add runtime summary coverage fields:

- `child_executor_dispatch_coverage.opt_in_ready_dispatch_status`
- `child_executor_dispatch_coverage.opt_in_ready_dispatch_ready`
- `child_executor_dispatch_coverage.opt_in_ready_handoff_ready`
- `child_executor_dispatch_coverage.opt_in_ready_will_dispatch`

## Safety

The dispatch contract remains descriptive only. Even when `dispatch_ready = true`, `will_dispatch` stays false and real invocation still requires an explicitly enabled `ChildExecutorDispatcher` plus a callable backend adapter.
