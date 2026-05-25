# Design

The guard belongs in `quality_gate_report.py` because it verifies the CI artifact shape at the point where the artifact is produced.

For any step that exposes runtime `contract_checks`, `_run_step()` will add:

```json
{
  "runtime_contract_artifact_schema": {
    "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
    "overall_status": "healthy",
    "summary_required_fields": ["..."],
    "summary_missing_fields": []
  }
}
```

The required fields mirror the backend snapshot guard for the quality gate summary:

- `overall_status`
- `check_count`
- `failed_check_count`
- `missing_payload_count`
- `approval_replay_coverage`
- `approved_tool_execution_coverage`
- `subagent_lane_query_detail_coverage`
- `subagent_lane_query_detail_coverage.detail_smoke`

If any path is missing, the schema status becomes `degraded`. Markdown rendering should expose the guard so CI artifacts can be inspected without parsing JSON.
