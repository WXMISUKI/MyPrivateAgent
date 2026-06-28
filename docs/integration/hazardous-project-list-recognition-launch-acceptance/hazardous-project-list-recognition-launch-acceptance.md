# Hazardous Project List Recognition Launch Acceptance

- Contract: `hazardous-project-list-recognition-launch-acceptance-v1`
- Decision: `go`
- Reason: `hazardous_project_list_recognition_ready_for_active_invocation`
- Next Action: `use_coze_workflow_capability_for_migration_smoke`
- Workflow Id: `hazardous_project_list_recognition`
- Capability Id: `coze.workflow.hazardous_project_list_recognition`
- Domain: `construction-safety`
- Owner: `szzg-owner@example.com`
- Generated At: `2026-06-26T00:00:00+08:00`

## Smoke Result

| Metric | Value |
|---|---|
| `ok` | `true` |
| `status` | `completed` |
| `http_status_code` | `n/a` |
| `run_id` | `run_931373be09524029bdd33bc5fe8b5a24` |
| `output_rows` | `14` |
| `expected_rows` | `14` |
| `match_status` | `match` |

## Input Fixture

| Field | Value |
|---|---|
| `fixture_name` | `副本危大工程清单测试文件.xlsx` |
| `fixture_type` | `spreadsheet` |
| `row_count` | `16` |
| `data_row_count` | `14` |

## Output Snapshot

```json
{
  "code": 200,
  "msg": "文件解析成功",
  "data_count": 14,
  "first_item": {
    "id": "1",
    "originname": "实施性施工组织设计",
    "name": "实施性施工组织设计",
    "category": "施工方案管理",
    "isExdanger": false
  },
  "last_item": {
    "id": "14",
    "originname": "钢箱梁专项施工方案",
    "name": "钢箱梁施工",
    "category": "其他类别",
    "isExdanger": false
  }
}
```

## Boundary

| Boundary | Value |
|---|---|
| `registry_read_only` | `true` |
| `default_chat_invocation` | `not_performed` |
| `model_invocation` | `performed_only_by_workflow_runtime` |
| `tool_execution` | `workflow_scoped_only` |
| `source_binding_creation` | `not_performed` |
| `memory_write` | `not_performed` |
| `audit_write` | `not_performed` |
| `trace_write` | `performed` |
| `runtime_behavior_changed` | `true` |

## Acceptance Notes

- This workflow was promoted from `review` to `active` for launch verification.
- The registry and invoke path both remain fail-closed for missing dependencies and invalid manifests.
- The acceptance sample is suitable as a reusable migration template for future Coze workflow onboarding.
- The repository-side regression suite passed after the status promotion.

## Workflow Lab Replay

This launch evidence can be replayed from `/workflow-lab` using `hazardous_project_list_sample`.

| Replay Item | Value |
|---|---|
| Workflow Id | `hazardous_project_list_recognition` |
| Capability Id | `coze.workflow.hazardous_project_list_recognition` |
| Example Id | `hazardous_project_list_sample` |
| Expected Comparison | `match` |
| Replay Boundary | `capability_runtime` |

Replay notes:

- The lab invocation should return the same normalized JSON contract as the production capability invoke path.
- The input reference should stay runtime-managed (`content_ref` / `artifact_id`) rather than a hard-coded local path.
- If the replay is blocked, the workflow should remain in `review` until the missing dependency or blocker is resolved.

## Blockers

None.

## Warnings

None.
