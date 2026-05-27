## Context

The failing Runtime Surface test creates a parent run, binds and executes a child executor, merges the child output, and then expects Runtime Surface to expose `risk_review` child merge semantics in both `runtime_core` and `governance_overview.run`.

Current child executor execution is intentionally fail-closed. `embedded_sdk_worker` execution requires explicit executor binding opt-in evidence. Without that evidence, binding is blocked, execution is blocked, merge is blocked, and `summarize_child_executor_merged_semantics(...)` has no persisted merged semantics to expose. Runtime Surface then surfaces the default normalized intent, `general_analysis`.

## Goals / Non-Goals

**Goals:**

- Make the integration fixture satisfy the same child executor prerequisites as production-like callers.
- Preserve fail-closed semantics for callers that do not opt in.
- Restore the previously failing Runtime Surface governance run-state test.
- Record the fixture contract in OpenSpec/docs so future tests do not silently drift.

**Non-Goals:**

- No production gate relaxation.
- No new child executor dispatch behavior.
- No Runtime Profile payload field changes.
- No broad rewrite of child executor merge semantics.

## Decisions

1. Fix the test fixture rather than the execution gate.

   Rationale: the gate is working as designed. The fixture asserts executed child merge semantics, so it must provide explicit execution opt-in evidence.

2. Keep the validation focused on the previously failing Runtime Surface test plus relevant SDK guard tests.

   Rationale: this is a fixture/contract alignment slice, not a broad child executor refactor.

3. Document this as a contract alignment, not a test-only workaround.

   Rationale: the fixture expresses an integration scenario. Its prerequisites are part of the contract between Runtime Surface tests and Embedded SDK child executor execution.

## Risks / Trade-offs

- [Risk] Updating the fixture could hide a real gate regression.
  Mitigation: keep existing SDK tests that assert missing opt-in remains blocked.

- [Risk] Runtime Surface tests may depend on child executor internals.
  Mitigation: only add the minimal opt-in evidence required for the existing scenario and avoid changing expected payload shape.
