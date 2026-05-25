# Design

## Contract Shape

The readiness contract is a backend assessment, not the detail read model itself:

```json
{
  "contract_version": "phase-h-subagent-lane-query-detail-readiness-v1",
  "channel": "subagent_lane",
  "readiness_status": "ready|blocked",
  "recent_summary_status": "recorded|no_records|unavailable",
  "ready_for_detail": true,
  "required_capabilities": {
    "stable_query_id": true,
    "stage_chain_candidate": true,
    "recent_summary_recorded": true,
    "separates_child_run_events": true
  },
  "blocking_reasons": [],
  "recommended_next_change": "subagent-lane-query-detail-contract"
}
```

## Source of Truth

The readiness contract should be derived from the existing `subagent_lane recent summary` builder and persisted Query Control timeline events. It must not ask the frontend to infer readiness from raw timeline entries.

## Readiness Rules

- `stable_query_id`: at least one summary item has a non-empty `query_id`.
- `stage_chain_candidate`: recorded subagent lane events expose stable lifecycle `stage` values.
- `recent_summary_recorded`: recent summary state is `recorded`.
- `separates_child_run_events`: query ids are represented through run/child-run identifiers rather than frontend-only labels.

If any capability is false, `ready_for_detail = false`, `readiness_status = blocked`, and `blocking_reasons` must be machine-readable.

## External References

- LangGraph checkpoint/resume informs the need to keep query identity stable before detail promotion; no graph runtime is introduced.
- Goose subagent isolation informs the distinction between child-run events and user-facing query detail; no subagent fan-out changes are introduced.
