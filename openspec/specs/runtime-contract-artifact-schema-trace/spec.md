# runtime-contract-artifact-schema-trace Specification

## Purpose
Ensure degraded runtime contract traces preserve artifact schema guard status and missing field evidence.
## Requirements
### Requirement: Degraded runtime contract trace MUST include artifact schema guard

`runtime_contract_gate_degraded` trace payloads MUST include normalized `runtime_contract_artifact_schema`.

#### Scenario: Artifact schema guard is present

- **WHEN** Runtime Contract Gate is degraded
- **AND** `runtime_contract_artifact_schema` is present
- **THEN** the trace payload includes normalized artifact schema fields

#### Scenario: Artifact schema guard is missing

- **WHEN** Runtime Contract Gate is degraded
- **AND** `runtime_contract_artifact_schema` is missing or malformed
- **THEN** the trace payload includes a stable default artifact schema object

### Requirement: Artifact schema guard MUST affect degraded trace fingerprint

The degraded trace fingerprint MUST include normalized `runtime_contract_artifact_schema`.

#### Scenario: Artifact schema status changes

- **WHEN** two degraded gate summaries differ only in artifact schema guard status or missing fields
- **THEN** they produce different fingerprints and therefore distinct dedupe keys
