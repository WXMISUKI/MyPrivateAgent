# Design

## Boundary

This change updates only the Health Router's governance trace payload/detail normalization for existing `runtime_contract_summary` fields. It does not introduce new runtime contract fields.

## Normalized Sections

The trace payload MUST preserve fail-closed normalized coverage for:

- `sdk_tool_runtime_execution_coverage`
- `embedded_sdk_persistence_coverage`
- `worker_ownership_store_mode_coverage`
- `child_executor_promotion_gate_coverage`
- `child_executor_execution_prerequisites_coverage`
- `child_executor_dispatch_coverage`
- `subagent_lane_query_detail_coverage`

Existing approval lifecycle, approved tool, checkpoint cursor, recovery retry, retry scheduler, and dispatcher coverage remain unchanged.

## Detail Labels

`runtime_contract_gate_degraded.detail` should include compact labels for the normalized sections so operators can scan trace rows without expanding payload:

`sdk_tool`, `embedded_persistence`, `worker_ownership`, `child_executor_gate`, `child_executor_prerequisites`, `child_executor_dispatch`, and `subagent_detail`.

## Failure Mode

Legacy or malformed sections are normalized to smoke flags of `false`. If the raw `runtime_contract_summary` itself is not an object, labels stay `unknown`.
