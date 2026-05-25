## ADDED Requirements

### Requirement: Runtime MUST gate worker ownership store mode coverage
The runtime contract quality gate MUST emit and summarize machine-readable evidence that the default worker ownership store mode remains conservative, configurable, and observable.

#### Scenario: Runtime smoke covers ownership store mode
- **WHEN** runtime contract smoke runs
- **THEN** it MUST emit a `worker_ownership_store_mode` check
- **AND** the check MUST prove the default mode is `memory_only`
- **AND** the check MUST prove the default ownership adapter is in-memory and non-durable
- **AND** the check MUST prove `WORKER_OWNERSHIP_STORE_MODE` is listed in configurable bootstrap knobs

#### Scenario: Quality gate summarizes ownership store mode coverage
- **WHEN** a quality gate report includes the `worker_ownership_store_mode` check
- **THEN** `runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke` MUST be true only when the check evidence is complete
- **AND** the summary MUST include the observed default mode, adapter kind, durability, strict mode status, and fallback mode status

#### Scenario: Missing ownership store mode coverage fails closed
- **WHEN** Runtime Contract Gate reads an old or dirty artifact without worker ownership store mode coverage
- **THEN** `runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke` MUST be false
- **AND** Runtime Contract Snapshot MUST report degradation if the coverage object or `mode_smoke` field is missing

