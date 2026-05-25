# Design

`RuntimeContractSnapshotService` already supports dot-path required fields, so this change should extend the existing `runtime_contract_gate` `ContractSnapshotSpec` instead of introducing a second validator.

Required nested paths:

- `runtime_contract_summary.overall_status`
- `runtime_contract_summary.check_count`
- `runtime_contract_summary.failed_check_count`
- `runtime_contract_summary.missing_payload_count`
- `runtime_contract_summary.approval_replay_coverage`
- `runtime_contract_summary.approved_tool_execution_coverage`
- `runtime_contract_summary.subagent_lane_query_detail_coverage`
- `runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke`

The service will continue reporting missing paths through the existing `missing_fields` list. This keeps consumers and tests aligned with the current snapshot model.
