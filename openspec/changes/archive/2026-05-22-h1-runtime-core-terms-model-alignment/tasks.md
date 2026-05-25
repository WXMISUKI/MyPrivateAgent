## 1. Runtime Core Terms Alignment

- [x] 1.1 Update `docs/architecture/runtime_contracts.md` to formalize `query / run / child run / scheduler run / approval / artifact / trace / audit`
- [x] 1.2 Update `docs/architecture/current_architecture.md` to reflect the Runtime Core object boundary and the `child_run_id` naming decision
- [x] 1.3 Update `docs/change/2026-05-16-phase-g-agent-runtime-reference-alignment.md` with the new Runtime Core terminology decision
- [x] 1.4 Update `docs/roadmap/next_phase_hardening.md` so the next priority explicitly returns to Runtime Core and read model convergence

## 2. Query / Run Read Model Consistency

- [x] 2.1 Update the `query-run-read-model` spec delta so query/run semantics explicitly align with the Runtime Core terminology
- [x] 2.2 Confirm `main_chat_query_detail` and `main_chat_query_history` contract interpretation stays shared across Runtime Surface and Governance Timeline
- [x] 2.3 Review any remaining docs or contract text that still treat `child_execution_id` as a primary term
- [x] 2.4 Record `child_display_id` as the formal display field for child run identity across runtime surface, approval, query-control, adapter timeline, and server serialization contracts

## 3. Verification and Completion

- [x] 3.1 Run focused documentation and spec validation by re-reading the updated artifacts
- [x] 3.2 Verify there is no contradiction between `runtime-core-terms-model` and `query-run-read-model`
- [x] 3.3 Prepare the change for implementation handoff once the spec passes self-review
