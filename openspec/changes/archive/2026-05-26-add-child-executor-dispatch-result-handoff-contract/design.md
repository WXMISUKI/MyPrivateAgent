## Context

The current child executor path has these boundaries:

- `child_executor_execution_prerequisites` blocks execution unless explicit executor binding, bounded context budget, and merge handoff semantics are present.
- `child_executor_dispatch_contract` blocks real dispatch unless promotion, prerequisites, and backend registry evidence are ready.
- `ChildExecutorDispatcher` is opt-in and invokes an injected backend adapter only when explicitly enabled.
- `child_executor_dispatch_attempt_handoff` validates sandbox attempt envelope readiness before adapter invocation.

The missing boundary is after adapter invocation: the dispatcher currently returns compact attempt data, but there is no named contract that says the backend result can be handed off to governance/audit while not being treated as parent merge, retry scheduling, or production worker enablement.

## Goals / Non-Goals

**Goals:**

- Add a `build_child_executor_dispatch_result_handoff_contract(...)` helper.
- Normalize successful sandbox attempt evidence, blocked dispatcher attempts, and malformed/unsafe results into compact machine-readable result handoff evidence.
- Preserve fail-closed behavior for missing backend result, malformed result, missing audit/output references, and unsafe payload results.
- Add runtime smoke and quality gate coverage proving ready, blocked, and malformed result handoff states.

**Non-Goals:**

- Do not start a child worker by default.
- Do not implement real sandbox execution or queueing.
- Do not merge child output into the parent run.
- Do not enable retry execution or auto-recovery for child executor dispatch.
- Do not add frontend UI or API endpoints.

## Decisions

1. Result handoff is a contract builder, not a new runtime executor.

   Rationale: the current hardening sequence is contract-first. A side-effect-free builder lets smoke/gate/snapshot consumers validate result shape before any production execution path is enabled.

2. Dispatcher attaches result handoff evidence but remains opt-in.

   Rationale: callers already use `ChildExecutorDispatcher.dispatch(...)` as the execution boundary. Attaching nested evidence there avoids a second interpretation path while preserving default disabled behavior.

3. Result handoff does not authorize parent merge.

   Rationale: merge semantics are already handled by `child_result_merge_handoff_contract`; backend output handoff must not claim that parent state has been updated.

4. Quality gate coverage is derived from runtime smoke fields.

   Rationale: this matches existing runtime contract hardening patterns and keeps Runtime Contract Gate and Snapshot aligned with the CI artifact.

## Risks / Trade-offs

- [Risk] Consumers may confuse result handoff with successful parent merge. -> Mitigation: expose `parent_merge_performed = false` and `merge_authorization = false` in the contract.
- [Risk] Dispatcher output shape grows. -> Mitigation: keep evidence compact and add snapshot coverage for stable fields only.
- [Risk] Existing tests assume raw backend result only. -> Mitigation: preserve `backend_result` and add nested `dispatch_result_handoff` evidence as an additive field.
