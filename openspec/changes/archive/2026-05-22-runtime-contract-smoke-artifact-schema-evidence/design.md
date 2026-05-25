# Design

Extend the existing `runtime_profile_contract_snapshot` smoke check payload with:

- `runtime_contract_artifact_schema_status`
- `runtime_contract_artifact_schema_missing_field_count`
- `runtime_contract_artifact_schema_missing_fields`

The check remains pass/fail based on the Runtime Profile contract snapshot being healthy. These fields are diagnostic evidence for CI artifacts and downstream quality gate summary parsing.
