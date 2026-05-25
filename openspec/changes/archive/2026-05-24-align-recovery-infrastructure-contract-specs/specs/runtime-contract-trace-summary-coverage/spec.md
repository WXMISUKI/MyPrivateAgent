## MODIFIED Requirements

### Requirement: Degraded runtime contract trace payload MUST preserve normalized coverage sections

The Health Router MUST normalize and write runtime contract summary coverage sections for SDK tool, embedded persistence, worker ownership, child executor gate, child executor prerequisites, child executor dispatch, child executor dispatcher, subagent detail, checkpoint cursor, recovery retry evidence, recovery retry scheduler, and durable recovery loader.

#### Scenario: Coverage sections are present

- **WHEN** `runtime_contract_gate.overall_status = degraded`
- **AND** the request has governance trace context
- **THEN** the persisted trace payload includes normalized coverage sections for each supported summary coverage field
- **AND** true smoke fields remain true only when their machine-readable evidence is present

#### Scenario: Coverage sections are missing

- **WHEN** a legacy or malformed summary omits one of the supported coverage sections
- **THEN** the persisted trace payload includes the section with its smoke flag set to false

### Requirement: Degraded runtime contract trace detail MUST expose compact coverage labels

The Health Router MUST include compact coverage labels in `runtime_contract_gate_degraded.detail` for the supported runtime contract summary sections, including `recovery_retry_scheduler`, `durable_loader`, and `child_executor_dispatcher`.

#### Scenario: Coverage is present

- **WHEN** a normalized smoke flag is true
- **THEN** the detail label for that section is `covered`

#### Scenario: Coverage is missing

- **WHEN** the raw runtime contract summary is present but a normalized smoke flag is false
- **THEN** the detail label for that section is `missing`

#### Scenario: Summary is unavailable

- **WHEN** the raw runtime contract summary is unavailable or malformed
- **THEN** the detail label for that section is `unknown`
