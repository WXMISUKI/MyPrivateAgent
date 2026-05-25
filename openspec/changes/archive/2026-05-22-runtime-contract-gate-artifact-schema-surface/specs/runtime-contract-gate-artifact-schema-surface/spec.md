# runtime-contract-gate-artifact-schema-surface

## ADDED Requirements

### Requirement: Runtime Contract Gate MUST expose quality gate artifact schema guard

`RuntimeContractGateService` MUST expose a normalized `runtime_contract_artifact_schema` object.

#### Scenario: Report includes schema guard

- **WHEN** the quality gate report step includes `runtime_contract_artifact_schema`
- **THEN** the runtime contract gate response includes the normalized guard
- **AND** `summary_missing_fields` is a list of strings

#### Scenario: Old report lacks schema guard

- **WHEN** the report has runtime contract checks and summary but no schema guard
- **THEN** the runtime contract gate response derives schema status from the normalized summary

#### Scenario: Report or checks are missing

- **WHEN** the quality gate report is missing or lacks runtime contract checks
- **THEN** the runtime contract gate response includes `runtime_contract_artifact_schema.overall_status = unknown`
