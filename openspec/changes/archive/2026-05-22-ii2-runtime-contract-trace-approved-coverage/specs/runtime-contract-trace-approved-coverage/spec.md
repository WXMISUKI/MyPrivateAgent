# runtime-contract-trace-approved-coverage

## ADDED Requirements

### Requirement: Degraded runtime contract trace MUST preserve approved tool coverage

`runtime_contract_gate_degraded` trace payloads MUST include normalized `runtime_contract_summary.approved_tool_execution_coverage`.

#### Scenario: Trace payload includes approved tool coverage

- **WHEN** Runtime Contract Gate is degraded and its summary contains approved tool coverage
- **THEN** the written trace payload includes `approved_tool_execution_coverage`
- **AND** approved and deny override fields are preserved in normalized compact form

### Requirement: Degraded runtime contract fingerprint MUST include approved tool coverage

Runtime Contract Gate degraded fingerprints and dedupe keys MUST change when approved tool bridge coverage changes.

#### Scenario: Approved tool coverage change writes a new trace

- **WHEN** two degraded Runtime Contract Gate profiles have the same failed checks but different `approved_tool_execution_coverage.bridge_smoke`
- **THEN** their fingerprints are different
- **AND** both degraded states can be recorded as distinct governance traces

### Requirement: Missing approved tool coverage MUST fail closed

Runtime Contract Gate degraded trace normalization MUST treat missing or malformed approved tool coverage as uncovered.

#### Scenario: Missing coverage is normalized as false

- **WHEN** Runtime Contract Gate summary has no object `approved_tool_execution_coverage`
- **THEN** the trace payload summary contains `approved_tool_execution_coverage.bridge_smoke = false`
