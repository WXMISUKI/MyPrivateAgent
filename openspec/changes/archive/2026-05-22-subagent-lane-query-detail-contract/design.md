# Design

## Contract Shape

The dedicated detail contract mirrors the proven main_chat detail boundary where appropriate, but stays channel-specific:

```json
{
  "contract_version": "phase-h-subagent-lane-query-detail-v1",
  "channel": "subagent_lane",
  "query_id": "frontend-child-p10-i23-c1",
  "recording_state": "recorded",
  "stage_chain": ["planning", "final_output"],
  "recent_events": [],
  "recent_event_count": 2,
  "latest_stage": "final_output",
  "latest_summary": "merged",
  "stage_count": 2,
  "warning_count": 0,
  "event_count": 2
}
```

## Source

The contract is derived from persisted Query Control traces filtered by `channel = subagent_lane` and matching `query_id`.

## Guardrails

- Missing `query_id` returns `recording_state = unavailable` and `reason = query_id_missing`.
- No matching events returns `recording_state = no_records` and `reason = query_id_not_found`.
- The contract may include compact recent events and stage chain, but must not include history pagination or workspace state.
- It must not replace child executor output replay or merged semantics contracts; those remain run/output oriented, while this contract is query-lifecycle oriented.
