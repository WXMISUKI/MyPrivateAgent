# Design

`RuntimeContractSnapshotService` already supports required dot-paths. Extend the `runtime_contract_gate` contract spec with:

- `runtime_contract_artifact_schema`
- `runtime_contract_artifact_schema.contract_version`
- `runtime_contract_artifact_schema.overall_status`
- `runtime_contract_artifact_schema.summary_required_fields`
- `runtime_contract_artifact_schema.summary_missing_fields`

The service will report missing paths using the existing `missing_fields` list. This keeps the new guard consistent with existing `runtime_contract_summary` nested snapshot behavior.
