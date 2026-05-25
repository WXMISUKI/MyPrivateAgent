# Design: subagent_lane query detail smoke gate

## Decision

Extend the existing runtime contract gate rather than creating a second gate. The runtime smoke script remains the sample source, `quality_gate_report.py` derives summary coverage from smoke checks, and `RuntimeContractGateService` normalizes the latest report for runtime profile consumers.

## Contract Shape

The smoke check MUST use a dedicated check name:

```json
{
  "name": "subagent_lane_query_detail",
  "ok": true,
  "contract_version": "phase-h-subagent-lane-query-detail-v1",
  "recording_state": "recorded",
  "query_id": "frontend-child-p10-i23-c1",
  "stage_count": 2,
  "recent_event_count": 2,
  "failure_reason": ""
}
```

The derived summary MUST include:

```json
{
  "subagent_lane_query_detail_coverage": {
    "detail_smoke": true,
    "contract_version": "phase-h-subagent-lane-query-detail-v1",
    "recording_state": "recorded",
    "stage_count": 2,
    "recent_event_count": 2
  }
}
```

## Boundaries

- This smoke check proves the contract shape and gate visibility, not full production data completeness.
- Missing or failed detail smoke should degrade runtime contract status like other runtime checks.
- The markdown report should show whether the detail smoke is covered without expanding the summary table into a general trace browser.
