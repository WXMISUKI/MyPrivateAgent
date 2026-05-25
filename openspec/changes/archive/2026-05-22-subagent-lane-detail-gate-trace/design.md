# Design: subagent lane detail gate trace

## Decision

Extend the existing runtime contract gate trace normalization path in `health.py`. The trace path already normalizes `approval_replay_coverage` and `approved_tool_execution_coverage`; `subagent_lane_query_detail_coverage` should follow the same fail-closed pattern.

## Contract Shape

The degraded trace payload MUST contain:

```json
{
  "runtime_contract_summary": {
    "subagent_lane_query_detail_coverage": {
      "detail_smoke": true,
      "contract_version": "phase-h-subagent-lane-query-detail-v1",
      "recording_state": "recorded",
      "stage_count": 2,
      "recent_event_count": 2
    }
  }
}
```

If the source summary is missing or malformed, it MUST normalize to:

```json
{
  "detail_smoke": false,
  "contract_version": "",
  "recording_state": "",
  "stage_count": 0,
  "recent_event_count": 0
}
```

## Dedupe

The fingerprint already hashes the normalized `runtime_contract_summary`. Once the new coverage is included there, a transition from `detail_smoke=false` to `detail_smoke=true` must produce a new fingerprint and therefore a new dedupe key.
