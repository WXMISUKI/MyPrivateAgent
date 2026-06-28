# SZZG Agent Encapsulation Route Launch Acceptance

- Contract: `szzg-agent-encapsulation-route-launch-acceptance-v1`
- Decision: `go`
- Reason: `szzg_agent_encapsulation_route_resolved`
- Next Action: `use_route_workflow_for_agent_jump_trials`
- Workflow Id: `szzg_agent_encapsulation_route`
- Capability Id: `coze.workflow.szzg_agent_encapsulation_route`
- Domain: `agent-orchestration`
- Owner: `szzg-owner@example.com`
- Generated At: `2026-06-26T17:43:00+08:00`

## Smoke Result

| Case | Input | Result |
|---|---|---|
| 示例1 | `打开代码调试助手` | `route_agent` |
| 示例2 | `查看我的收藏` | `route_square` |
| 示例3 | `当前有哪些适合监理的智能体` | `clarify_multi` |
| 示例4 | `打开图片处理大师` | `clarify_none` |

## Case Details

### 示例1：单个智能体跳转

Input:

```json
{
  "user_input": "打开代码调试助手",
  "data": [
    {
      "agentId": "7",
      "agentName": "代码调试助手"
    }
  ]
}
```

Output:

```json
{
  "command": "route_agent",
  "params": ["ROUTE://agent_detail?id=7"],
  "message": "我马上为你打开代码调试助手智能体"
}
```

### 示例2：广场收藏页跳转

Input:

```json
{
  "user_input": "查看我的收藏"
}
```

Output:

```json
{
  "command": "route_square",
  "params": ["ROUTE://square_page?page=collect"],
  "message": "这就为你打开收藏列表页面"
}
```

### 示例3：多匹配反问

Input:

```json
{
  "user_input": "当前有哪些适合监理的智能体",
  "data": [
    {
      "agentId": "11",
      "agentName": "监理日志编写助手"
    },
    {
      "agentId": "12",
      "agentName": "施工方案审查"
    }
  ]
}
```

Output:

```json
{
  "command": "clarify_multi",
  "params": ["监理日志编写助手", "施工方案审查"],
  "message": "为你找到以下匹配的智能体，请告诉我具体要打开哪一个"
}
```

### 示例4：无匹配智能体

Input:

```json
{
  "user_input": "打开图片处理大师",
  "data": []
}
```

Output:

```json
{
  "command": "clarify_none",
  "params": [],
  "message": "未找到对应智能体，请确认名称后再试哦"
}
```

## Boundary

| Boundary | Value |
|---|---|
| `registry_read_only` | `true` |
| `invoke_path` | `active` |
| `default_chat_invocation` | `not_performed` |
| `model_invocation` | `workflow_scoped_only` |
| `tool_execution` | `workflow_scoped_only` |
| `source_binding_creation` | `not_performed` |
| `memory_write` | `not_performed` |
| `audit_write` | `not_performed` |
| `trace_write` | `performed` |

## Acceptance Notes

- The workflow is now a reusable template for agent-plaza routing and square-page jump scenarios.
- Input format is `user_input + optional data[]`, output format is `command + params + message`.
- Registry and invocation both passed after promoting the workflow to `active`.
- This workflow can be used as a standard sample for future route-type Coze migrations.

## Workflow Lab Replay

The same four cases can be replayed from `/workflow-lab` using the exact input payloads above.

| Example | Replay Source | Expected Comparison |
|---|---|---|
| 示例1 | `route_agent_single_match` | `match` |
| 示例2 | `route_square_collect` | `match` |
| 示例3 | `clarify_multi_match` | `match` |
| 示例4 | `clarify_none_match` | `match` |

Replay boundary:

- The lab uses the `coze.workflow.szzg_agent_encapsulation_route` capability envelope.
- The replay result should include `run_id`, `status`, `trace_summary`, and `expected_comparison`.
- A blocked replay means the workflow is not ready for promotion and should remain in `draft` or `review`.

## Re-run Command

Run the same four cases in `myenv`:

```powershell
conda run -n myenv python -m pytest backend/tests/coze_workflow_registry_test.py -q
```

For direct invocation checks, the route scenarios should return:

- `route_agent` for a single matched agent
- `route_square` for the collection page jump
- `clarify_multi` for multiple matches
- `clarify_none` for no matches

If a dependency such as `http.request` is missing in a future workflow, record the blocker explicitly and either map it to a supported executor or keep the workflow blocked until the runtime contract is updated.

## Blockers

None.

## Warnings

None.
