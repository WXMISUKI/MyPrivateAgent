# Runtime Plane Stage 1 Slice Review - Tool Agent

> 这是 Stage 1 第二个最小切片 `tool_agent` 的实际回顾。它只验证受控单工具闭环，没有越级到审批、多智能体或通用工具平台。

## Stage

Stage 1 - Runtime MVP, Slice 2 (`tool_agent`)

## Date

2026-07-09

## Owner

MyPrivateAgent maintainers

## Completed Work

- 新增 `backend/runtime_plane/adapters/tool_agent.py`
- `ToolAgentAdapter` 已能把一个本地 `Agent` 跑成标准化 tool execution envelope
- 新增 focused tests：`backend/tests/runtime_plane/test_tool_agent_adapter.py`
- 运行验证通过：`python -m pytest backend/tests/runtime_plane -q`

## What Stayed Within Scope

- 只验证单个受控工具闭环
- 只验证 tool schema、tool call、tool observation 与 normalized envelope
- 没有引入审批分支
- 没有引入多智能体路由
- 没有把运行层扩成通用工具平台

## What Drifted or Got Tempting

- `Agent` 和 graph engine 已经支持更复杂的 handoff / subgraph，容易让人顺手继续加多智能体能力
- 工具节点天然很容易扩到完整编排器，所以必须继续守住“只做最小受控工具闭环”的边界

## What Evidence Shows the Slice Is Done

- `backend/tests/runtime_plane/test_tool_agent_adapter.py` 通过
- `backend/tests/runtime_plane/test_simple_agent_adapter.py` 仍通过
- `docs/roadmap/runtime_plane_stage_1_tool_agent_selection.md` 已锁定这条切片的边界和非目标

## What Must Not Be Expanded Next

- 不要把这个切片直接扩成 approval agent
- 不要把审批逻辑塞进这个切片
- 不要把它升级成通用工具平台或多智能体编排平台

## Is the Next Stage Still Justified

Yes。下一步仍然是 Stage 1 的后续切片，但必须先确认 tool_agent 这个最小边界已经稳定。

## Next Allowed Action

- 先复盘 `tool_agent` 的 envelope 设计是否还要补字段
- 再决定是否进入 `approval_agent`
- 如果进入 `approval_agent`，仍然必须通过 adapter boundary，不得绕过标准合同

## Rollback or Pause Condition

- 一旦 `tool_agent` 开始承载审批或多智能体路由，就说明切片边界失守，必须暂停并回到战略边界
