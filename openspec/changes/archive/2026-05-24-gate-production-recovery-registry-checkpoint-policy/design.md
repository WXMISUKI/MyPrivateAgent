## Design

### Production Policy Contract

The new policy contract should be a compact builder that proves two readiness sections are governed:

- registry binding resolution:
  - requires stable binding identity
  - requires all executable reattach to go through the continuation registry
  - forbids callable deserialization
  - treats unresolved bindings as fail-closed
- checkpoint/resume cursor gate:
  - requires a checkpoint contract
  - requires a resume cursor contract
  - requires state-gated cursor semantics
  - treats stale/resolved approval state as fail-closed

The contract is static policy evidence. It does not inspect a specific run and does not execute recovery.

### Production Gate Semantics

`build_embedded_sdk_persistence_interface()` can mark `registry_binding_resolution` and `checkpoint_resume_cursor_gate` ready because the runtime now has:

- `EmbeddedContinuationRegistry` binding identity and catalog evidence
- `DurableRecoveryLoader` registry-backed candidate evidence
- `checkpoint` and `resume_cursor` contracts
- runtime smoke and quality gate coverage for ready and blocked/stale paths

The durable workspace production recovery gate must still remain blocked by worker ownership production gate and rollout.

### Quality Gate Semantics

Runtime smoke will emit policy readiness evidence as part of the embedded persistence posture check. Quality Gate and Runtime Contract Gate normalize that evidence into `production_recovery_registry_checkpoint_policy_coverage.policy_smoke` and fail closed for old or dirty reports.

### Non-Goals

- No production cross-process recovery executor.
- No automatic recovery handoff execution.
- No worker ownership lease validation.
- No callable deserialization or persisted callable execution.
