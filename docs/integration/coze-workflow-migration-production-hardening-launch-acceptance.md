# Coze Workflow Migration Production Hardening Launch Acceptance

## Scope

This record captures the production-hardening acceptance sample for the Coze route workflow migration path.

- Workflow: `szzg_agent_encapsulation_route`
- Stable capability id: `coze.workflow.szzg_agent_encapsulation_route`
- Runtime boundary: `capability_runtime`
- Verification surface: registry, dependency mapping, Workflow Lab replay, and production invoke envelope

## Verification Command

```powershell
conda run -n myenv --no-capture-output python -m pytest backend/tests/coze_workflow_lab_test.py backend/tests/coze_workflow_registry_test.py -q
```

Result:

- `26 passed`

> 注：本记录保留为迁移样板，后续依赖映射门禁或验收样例扩展时，只需要更新同一条 focused pytest 命令和结果摘要即可，不必新建另一份重复文档。

## Canonical Route Scenarios

### Scenario 1: Single Agent Jump

Input:

```json
{
  "user_input": "打开代码调试助手",
  "data": [{"agentId": "7", "agentName": "代码调试助手"}]
}
```

Expected output:

```json
{
  "command": "route_agent",
  "params": ["ROUTE://agent_detail?id=7"],
  "message": "我马上为你打开代码调试助手智能体"
}
```

### Scenario 2: Square Favorites Page

Input:

```json
{
  "user_input": "查看我的收藏"
}
```

Expected output:

```json
{
  "command": "route_square",
  "params": ["ROUTE://square_page?page=collect"],
  "message": "这就为你打开收藏列表页面"
}
```

### Scenario 3: Multi-match Clarification

Input:

```json
{
  "user_input": "当前有哪些适合监理的智能体"
}
```

Matched candidates:

- `监理日志编写助手`
- `施工方案审查`

Expected output:

```json
{
  "command": "clarify_multi",
  "params": ["监理日志编写助手", "施工方案审查"],
  "message": "为你找到以下匹配的智能体，请告诉我具体要打开哪一个"
}
```

### Scenario 4: No Match

Input:

```json
{
  "user_input": "打开图片处理大师"
}
```

Expected output:

```json
{
  "command": "clarify_none",
  "params": [],
  "message": "未找到对应智能体，请确认名称后再试哦"
}
```

## Runtime Boundary

- Dependency mapping must classify route nodes explicitly.
- `http.request` should be surfaced as a runtime capability when supported, otherwise the workflow must remain blocked with a machine-readable blocker reason.
- Production invoke must preserve the shared envelope returned by capability runtime.
- Draft and review states must fail closed.

## Dependency Enforcement Acceptance

### Scenario 5: Provider-backed dependency is unavailable

Input:

```json
{
  "input": "hello"
}
```

Workflow manifest excerpt:

```yaml
dependencies:
  providers:
    - missingProvider
```

Expected invoke outcome:

```json
{
  "ok": false,
  "status": "blocked",
  "error": {
    "code": "COZE_WORKFLOW_DEPENDENCY_UNAVAILABLE",
    "blockers": ["provider_not_ready:missingProvider"]
  }
}
```

### Scenario 6: Shared dependency contract is identical in registry and Workflow Lab

Expected read model:

- registry detail and Workflow Lab detail expose the same `dependency_summary`
- registry detail and Workflow Lab detail expose the same `dependency_mapping`
- unsupported nodes are surfaced as `explicit_blocker`
- ready provider-backed nodes are surfaced as `provider_backed`

## Handoff Notes

- Use the Workflow Lab replay result as the canonical review artifact before promotion.
- Keep model/provider registry work separate from this route sample.
- If the workflow output diverges from the expected JSON, keep the workflow in review until the blocker or fixture is corrected.
- If dependency mapping introduces a blocker, fix the manifest or the provider readiness first; do not bypass the block in invoke logic.
