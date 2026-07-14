# Runtime Plane Stage 1 Slice Review - Approval Agent

> 这是 Stage 1 第三个最小切片 `approval_agent` 的实际回顾。它只验证高风险工具意图能被归一化为 approval-pending envelope，没有进入真实审批提交或恢复执行。

## Stage

Stage 1 - Runtime MVP, Slice 3 (`approval_agent`)

## Date

2026-07-14

## Owner

MyPrivateAgent maintainers

## Completed Work

- 新增 `backend/runtime_plane/adapters/approval_agent.py`
- `ApprovalAgentAdapter` 已能把高风险工具意图转换为标准化 approval interrupt envelope
- 新增 focused tests：`backend/tests/runtime_plane/test_approval_agent_adapter.py`
- 运行验证通过：`python -m pytest backend/tests/runtime_plane/test_simple_agent_adapter.py backend/tests/runtime_plane/test_tool_agent_adapter.py backend/tests/runtime_plane/test_approval_agent_adapter.py`

## What Stayed Within Scope

- 只验证 `approval_pending` envelope
- 只读取模型第一步 tool intent
- 高风险工具 handler 没有执行
- 没有提交生产审批
- 没有实现 approval resume
- 没有改变默认 `/api/chat`
- 没有引入 scheduler、sandbox、checkpoint 或 managed runtime

## What Drifted or Got Tempting

- `approval_pending` 很容易被误读为“审批系统已经接好”
- 下一步也很容易顺手做 resume 或真实 ApprovalEngineService 写入
- 这些都应另开 change，并先明确 replay / audit / policy / recovery 边界

## What Evidence Shows the Slice Is Done

- `ApprovalAgentAdapter.health_check()` 对无 approval-capable tool 的 agent 保持 blocked
- 高风险工具调用返回 `ExecutionResult.status = approval_pending`
- approval event 使用 `stage = approval` 与 `type = approval_required`
- event metadata 只包含 compact request/tool/risk/permission/reason/args summary
- 测试证明高风险工具 handler 未执行

## What Must Not Be Expanded Next

- 不要在当前切片里补真实审批提交
- 不要直接做 approved continuation
- 不要把 local graph engine 扩成生产 human-in-loop runtime
- 不要把该 adapter 接入默认 main chat

## Is the Next Stage Still Justified

Yes。Stage 1 三条 MVP 竖切已经闭合，下一阶段可以进入只读治理接线或 framework adapter authoring template。继续扩本地运行引擎的收益开始下降，平台膨胀风险开始上升。

## Next Allowed Action

- 优先做 Runtime Plane governance bridge read-only wiring，让 Stage 1 envelope 进入治理可见层
- 或者先做 framework adapter authoring template，把 local adapter proof 转成 LangGraph / AgentRun adapter 的开发规范
- 若要做真实审批提交或恢复执行，必须新开显式 OpenSpec change

## Rollback or Pause Condition

- 一旦 `approval_agent` 开始创建生产审批、恢复执行或写入 worker/scheduler/checkpoint 状态，就说明切片边界失守，必须暂停并回到 runtime-plane integration strategy。
