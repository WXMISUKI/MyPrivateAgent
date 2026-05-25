## 1. OpenSpec Contract

- [x] 1.1 Create proposal, design, specs, and tasks for durable runtime checkpoint/resume cursor
- [x] 1.2 Validate the new OpenSpec change in strict mode

## 2. Backend Contract

- [x] 2.1 Add focused tests for checkpoint status on durable and non-durable workspace backends
- [x] 2.2 Add focused tests for resume cursor readiness through registry binding
- [x] 2.3 Add focused tests for stale/state-gated cursors on approved and denied approvals
- [x] 2.4 Implement checkpoint derivation in the embedded workspace/recovery seam
- [x] 2.5 Implement resume cursor derivation in `EmbeddedAgentRuntimeSDK.probe_run_recovery(...)`
- [x] 2.6 Preserve checkpoint and cursor fields through `RuntimeSurfaceService.get_run_recovery(...)`

## 3. Runtime Contract Gate

- [x] 3.1 Extend `runtime_contract_smoke.py` with durable checkpoint/resume cursor alignment evidence
- [x] 3.2 Extend `quality_gate_report.py` with checkpoint/resume cursor coverage summary
- [x] 3.3 Extend `RuntimeContractGateService` and `RuntimeContractSnapshotService` guards for the new summary field
- [x] 3.4 Add degraded trace detail/fingerprint coverage for checkpoint recovery drift when the gate is degraded

## 4. Docs and Verification

- [x] 4.1 Update `docs/architecture/runtime_contracts.md`
- [x] 4.2 Update `docs/roadmap/next_phase_hardening.md`
- [x] 4.3 Update `docs/test_manual.md`
- [x] 4.4 Run focused backend regression in `myenv`
- [x] 4.5 Mark all tasks complete after verification
