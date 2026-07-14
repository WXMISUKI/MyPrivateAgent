# Runtime Plane Governance Read Model Review

> 这是 Stage 1 之后的第一刀治理可见性切片。它只把 runtime-plane adapter envelope 投影成 compact governance read model，没有进入 trace persistence、Runtime Surface API 或生产审批。

## Stage

Post Stage 1 - Read-only Governance Projection

## Date

2026-07-14

## Owner

MyPrivateAgent maintainers

## Completed Work

- 新增 `build_runtime_plane_governance_projection(...)`
- `GovernanceBridge.project_execution_envelope(...)` 已提供 side-effect-free projection 入口
- `SimpleAgentAdapter.execute(...)`、`ToolAgentAdapter.execute(...)`、`ApprovalAgentAdapter.execute(...)` 已返回 top-level `governance_projection`
- 新增 focused tests：`backend/tests/runtime_plane/test_governance_projection.py`

## What Stayed Within Scope

- 只读 projection
- 只消费 `ExecutionRequest / AgentManifest / ExecutionEvent / ExecutionResult`
- 只输出 compact identity、status、stage counts、tool/approval indicators 和 boundary flags
- 没有写 trace/audit
- 没有提交审批
- 没有接 Runtime Surface API
- 没有改变默认 `/api/chat`

## What Drifted or Got Tempting

- 很容易把 projection 直接接入 Runtime Surface 或 Governance Timeline
- 很容易把 `approval_required` projection 误读成真实审批请求已经创建
- 这些后续都必须另开 change，并先明确持久化、审计、回放和前端消费边界

## What Evidence Shows the Slice Is Done

- `test_governance_projection.py` 覆盖 simple/tool/approval 三类 adapter
- simple projection 验证 read-only boundary flags
- tool projection 验证 `tool_call_count`
- approval projection 验证 `approval_required` 与 `approval_tool_name`
- 聚焦测试通过：`python -m pytest backend/tests/runtime_plane/test_simple_agent_adapter.py backend/tests/runtime_plane/test_tool_agent_adapter.py backend/tests/runtime_plane/test_approval_agent_adapter.py backend/tests/runtime_plane/test_governance_projection.py`

## What Must Not Be Expanded Next

- 不要在当前 projection 中写数据库
- 不要把 projection 当成 persisted trace
- 不要在当前切片里接审批提交或 resume
- 不要直接改默认 main chat

## Is the Next Stage Still Justified

Yes。现在 runtime-plane MVP 已有最小治理摘要，下一步可以选择 Runtime Surface 只读 profile 或 framework adapter authoring template。继续扩本地 graph engine 的价值低于把 adapter 开发规范和治理消费边界固定下来。

## Next Allowed Action

- 优先做 Runtime Surface read-only profile for runtime-plane projections
- 或者做 Framework adapter authoring template，把 local proof 固化为 LangGraph / AgentRun adapter 模板
- 若要写 trace/audit 或提交审批，必须另开显式 OpenSpec change

## Rollback or Pause Condition

- 一旦 projection 开始写 trace/audit、创建审批、启动 worker/scheduler 或改变 chat 行为，就说明切片越界，必须暂停并回到 runtime-plane integration strategy。
