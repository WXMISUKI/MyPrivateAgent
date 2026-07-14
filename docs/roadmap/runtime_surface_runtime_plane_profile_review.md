# Runtime Surface Runtime Plane Profile Review

> 这是 Runtime Plane governance projection 之后的 Runtime Surface 只读消费入口切片。它让控制面能看到 projection contract readiness，但不执行 adapter、不保存 projection、不写 trace/audit。

## Stage

Post Stage 1 - Runtime Surface Read-only Profile

## Date

2026-07-14

## Owner

MyPrivateAgent maintainers

## Completed Work

- 新增 `backend/services/runtime_surface_runtime_plane_builder.py`
- Runtime Surface 顶层 profile 新增 `runtime_plane_governance_profile`
- Runtime Contract Snapshot 新增该 profile 的稳定字段守护
- 新增/更新 focused tests：
  - `tests/agent_framework/test_runtime_surface_service.py`
  - `tests/agent_framework/test_runtime_contract_snapshot_service.py`

## What Stayed Within Scope

- 只读 Runtime Surface profile
- 默认不携带 latest projection，并明确 `projection_source_unavailable`
- supplied projection 只做 compact summary
- 没有执行 runtime-plane adapter
- 没有写 trace/audit
- 没有提交审批
- 没有改默认 `/api/chat`
- 没有新增前端 UI

## What Drifted or Got Tempting

- 很容易把 profile 直接接到 Governance Timeline
- 很容易把 latest projection summary 误读为 persisted trace
- 很容易顺手做 live adapter invocation
- 这些都必须另开 change，并先明确持久化、审计和回放边界

## What Evidence Shows the Slice Is Done

- Runtime Surface builder 默认返回 `latest_projection_available = false`
- supplied projection 会被压缩为 compact latest summary，且不复制 raw state
- Runtime Surface `get_runtime_profile()` 返回 `runtime_plane_governance_profile`
- Runtime Contract Snapshot 会在缺失 boundary 字段时 degraded
- 聚焦测试通过：`python -m pytest tests/agent_framework/test_runtime_surface_service.py tests/agent_framework/test_runtime_contract_snapshot_service.py`

## What Must Not Be Expanded Next

- 不要在 profile builder 里执行 adapters
- 不要把 profile 当 persisted trace
- 不要在当前切片里提交审批或 resume
- 不要直接接默认 main chat

## Is the Next Stage Still Justified

Yes。Runtime Surface 已有只读 projection profile，下一步更适合做 Framework adapter authoring template，或者先写 trace-backed projection source proposal。继续扩本地 graph/checkpoint/scheduler 的收益低且风险高。

## Next Allowed Action

- 优先做 Framework adapter authoring template
- 或者做 trace-backed projection source proposal
- 若要写 trace/audit 或提交审批，必须另开显式 OpenSpec change

## Rollback or Pause Condition

- 一旦 `runtime_plane_governance_profile` 开始执行 adapter、写数据库、创建审批或改变 chat 行为，就说明切片越界，必须暂停并回到 runtime-plane integration strategy。
