## 1. Contract Helpers

- [x] 1.1 Add focused tests for deriving `memory_preview`, `durable_ready`, and `durable_degraded` persistence postures from workspace backend descriptions.
- [x] 1.2 Implement a small backend helper/builder that normalizes persistence posture without reading private workspace store internals.
- [x] 1.3 Preserve existing `workspace_backend.state_contract` vocabulary and avoid changing durable/runtime-only state kind names.

## 2. SDK and Facade Bootstrap

- [x] 2.1 Add focused tests proving `EmbeddedRuntimeFactory.create_sdk(...)` and `create_agent(...)` share the same persistence dependency source.
- [x] 2.2 Expose the normalized persistence interface through the SDK/factory runtime contract path.
- [x] 2.3 Ensure SDK/facade construction does not treat ad hoc constructor flags as proof of durable recovery support.

## 3. Recovery Alignment

- [x] 3.1 Add tests for recovery probes under memory preview, durable ready without descriptor, and durable degraded/fallback states.
- [x] 3.2 Include compact persistence evidence in recovery probe results and blocked recovery metadata.
- [x] 3.3 Keep recovery fail-closed: durable readiness must not bypass descriptor, registry binding, approval state, checkpoint, or cursor gates.

## 4. Runtime Surface and Contract Gate

- [x] 4.1 Thread the persistence interface into Runtime Surface without removing existing `workspace_backend`, `run_recovery`, checkpoint, or cursor fields.
- [x] 4.2 Add a focused `runtime_contract_smoke.py` check for embedded SDK persistence posture coverage.
- [x] 4.3 Add quality gate and Runtime Contract Gate summary normalization for persistence posture coverage.
- [x] 4.4 Add Runtime Contract Snapshot guard fields only after the summary shape is stable.

## 5. Docs and Verification

- [x] 5.1 Update `docs/architecture/runtime_contracts.md` with the SDK persistence interface contract and recovery separation rules.
- [x] 5.2 Update `docs/roadmap/next_phase_hardening.md` with current progress and follow-up boundaries.
- [x] 5.3 Update `docs/test_manual.md` with focused verification notes.
- [x] 5.4 Run `cmd /c openspec validate define-embedded-sdk-persistence-interface --strict`.
- [x] 5.5 Run focused backend tests in `myenv`, expected starting point: `conda run -n myenv python -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_embedded_workspace_store tests.agent_framework.test_runtime_surface_service -v`.
- [x] 5.6 Run focused gate tests if gate files are touched: `conda run -n myenv python -m unittest tests.agent_framework.test_runtime_contract_smoke tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_quality_gate_report -v`.
