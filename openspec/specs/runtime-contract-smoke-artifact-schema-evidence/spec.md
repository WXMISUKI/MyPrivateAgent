# runtime-contract-smoke-artifact-schema-evidence Specification

## Purpose
Ensure runtime contract smoke output carries artifact schema evidence for quality gate reporting.
## Requirements
### Requirement: Runtime profile snapshot smoke check MUST expose artifact schema evidence

The `runtime_profile_contract_snapshot` smoke check MUST include machine-readable artifact schema evidence from Runtime Contract Gate.

#### Scenario: Runtime profile includes artifact schema guard

- **WHEN** `/api/runtime-profile` returns `runtime_contract_gate.runtime_contract_artifact_schema`
- **THEN** the smoke check includes `runtime_contract_artifact_schema_status`
- **AND** it includes `runtime_contract_artifact_schema_missing_field_count`
- **AND** it includes `runtime_contract_artifact_schema_missing_fields`

#### Scenario: Runtime profile lacks artifact schema guard

- **WHEN** `/api/runtime-profile` lacks artifact schema guard
- **THEN** the smoke check still includes stable default artifact schema evidence fields
