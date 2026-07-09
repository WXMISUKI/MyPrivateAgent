# Runtime Plane Stage 1 Slice Review

> 这是 Stage 1 第一个最小切片 `simple_agent` 的实际回顾。它只验证 envelope 和 adapter boundary，没有越级到工具、审批或多智能体。

## Stage

Stage 1 - Runtime MVP, Slice 1 (`simple_agent`)

## Date

2026-07-08

## Owner

MyPrivateAgent maintainers

## Completed Work

- 新增 `backend/runtime_plane/contracts/execution.py`
- `ExecutionRequest / ExecutionEvent / ExecutionResult / AgentManifest` 已落地
- 新增 `backend/runtime_plane/adapters/simple_agent.py`
- `SimpleAgentAdapter` 已能把一个本地 `Agent` 跑成标准化 execution envelope
- 新增 focused tests：`backend/tests/runtime_plane/test_simple_agent_adapter.py`
- 运行验证通过：`python -m pytest backend/tests/runtime_plane/test_simple_agent_adapter.py -q`

## What Stayed Within Scope

- 只验证 request / event / result / manifest 这组标准合同
- 只验证单个 agent 的最小运行路径
- 没有引入工具调用
- 没有引入审批分支
- 没有把运行层做成平台克隆

## What Drifted or Got Tempting

- 运行层骨架里已经有 graph / bootstrap / bridge 代码，容易让人顺手继续补更大的执行能力
- 现有 `Agent`/`GraphEngine` 本身已经很强，容易在第一切片里不小心滑向 tool/approval/streaming 的复杂化

## What Evidence Shows the Slice Is Done

- `backend/tests/runtime_plane/test_simple_agent_adapter.py` 通过
- `backend/scripts/runtime_plane_smoke.py` 仍保持通过
- `docs/architecture/runtime_plane_integration_strategy.md` 已把 `simple_agent` 标成 Stage 1 首切片

## What Must Not Be Expanded Next

- 不要把这个切片直接扩成 tool agent
- 不要把审批逻辑塞进这个切片
- 不要在这个切片里引入真实 provider 依赖

## Is the Next Stage Still Justified

Yes. 下一步仍然是 Stage 1 的后续切片，但必须先确认 simple_agent 这个最小边界已经稳定。

## Next Allowed Action

- 先复盘 `simple_agent` 的 envelope 设计是否还要补字段
- 再决定是否进入 `tool_agent`
- 如果进入 `tool_agent`，仍然必须通过 adapter boundary，不得绕过标准合同

## Rollback or Pause Condition

- 一旦 `simple_agent` 开始被要求处理工具调用或审批，就说明切片边界失守，必须暂停并回到战略边界
