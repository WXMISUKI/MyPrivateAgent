## Context

The current child executor path intentionally stops at a relationship seam. The system already exposes child executor preflight and promotion gate contracts, and the latest quality gate can prove that the default gate remains relationship-only. The missing boundary is a compact contract that lists the execution prerequisites needed before a real child executor may be connected.

## Goals / Non-Goals

**Goals:**

- Add a compact, backend-owned `child_executor_execution_prerequisites` contract.
- Derive readiness from existing preflight/gate signals, not from frontend or caller recomputation.
- Keep default behavior blocked and relationship-only.
- Add quality gate and snapshot evidence so malformed or missing prerequisite contracts fail closed.

**Non-Goals:**

- Starting a real child executor.
- Implementing executor scheduling, sandboxing, worker lease enforcement, or database migrations.
- Changing existing child output merge behavior.

## Decisions

1. Nest the prerequisites contract under the existing promotion gate surface.

   Rationale: the gate is the final yes/no boundary for leaving the relationship seam. Nesting keeps consumers on one contract path and avoids adding a parallel top-level runtime profile section for the same decision.

2. Use a requirements list plus derived summary fields.

   Rationale: a list of `{name, status, evidence, blocker}` entries is extensible, while summary fields such as `ready`, `overall_status`, and `missing_requirements` make smoke tests and UI consumers simple.

3. Keep prerequisite evaluation side-effect free.

   Rationale: this slice is about observability and gating. It must not create child runs, mutate continuation state, or imply executor startup.

4. Add quality-gate coverage from runtime contract smoke.

   Rationale: the readiness contract is a production safety boundary. Missing or malformed evidence should be visible in `runtime_contract_summary`, Runtime Contract Gate, and snapshot checks.

## Risks / Trade-offs

- Contract duplication risk -> Mitigate by deriving prerequisites from preflight/gate builder outputs and documenting promotion gate as the consumer entrypoint.
- Over-promising readiness risk -> Mitigate with default fail-closed statuses and explicit relationship-only blockers.
- Broader quality gate churn -> Mitigate with a focused smoke check and one nested summary field.
