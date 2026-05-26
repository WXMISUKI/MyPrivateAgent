## Context

Current child executor execution is intentionally relationship-only by default. The sandbox worker backend adapter contract already defines guard evidence and compact dispatch attempts, and `ChildExecutorDispatcher` already blocks unsafe sandbox payloads. However, the runtime contract evidence chain currently tracks the generic dispatcher check, not a dedicated sandbox backend adapter coverage signal.

This change promotes the sandbox adapter readiness evidence into the same quality-gate path used by other Runtime Core contracts.

## Goals / Non-Goals

**Goals:**

- Add a dedicated runtime smoke check for sandbox worker backend adapter readiness and fail-closed behavior.
- Normalize that check into `runtime_contract_summary.child_executor_sandbox_backend_coverage`.
- Make Runtime Contract Gate and Snapshot degrade when sandbox backend adapter coverage is missing or inconsistent.
- Keep all behavior side-effect-free unless the dispatcher is explicitly enabled inside the smoke check.

**Non-Goals:**

- No default child executor dispatch.
- No real sandbox process, queue, worker lifecycle, or remote executor binding.
- No durable workspace, continuation recovery, or database migration.
- No frontend-side readiness derivation.

## Decisions

- Use a separate coverage object instead of overloading `child_executor_dispatcher_coverage`.
  - Rationale: dispatcher readiness and sandbox adapter guard readiness are related but distinct. Keeping them separate makes missing sandbox guard evidence visible without weakening the existing dispatcher signal.
  - Alternative considered: add extra fields to dispatcher coverage. Rejected because it would blur generic dispatcher behavior with sandbox-specific contract requirements.

- Treat incomplete guard evidence, unsafe payload, malformed attempt output, and adapter invocation count as first-class smoke evidence.
  - Rationale: the canonical spec requires fail-closed semantics and compact attempt evidence before real dispatch can be considered.
  - Alternative considered: only verify adapter contract helper tests. Rejected because helper tests do not prove the runtime contract artifact can catch regressions.

- Keep the smoke adapter in-memory and deterministic.
  - Rationale: this verifies the contract boundary without introducing worker lifecycle side effects.

## Risks / Trade-offs

- Runtime summary grows by one nested coverage object -> Mitigation: keep the object compact and only include machine-readable fields needed by gate/snapshot consumers.
- Existing tests may need fixture updates -> Mitigation: update only runtime contract fixtures that represent the full summary schema.
- Coverage can be mistaken for production readiness -> Mitigation: explicitly document that this is adapter gate coverage, not default worker enablement.
