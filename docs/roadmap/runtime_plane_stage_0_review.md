# Runtime Plane Stage 0 Review

> 这是 Stage 0 冻结与定位收口的实际回顾样本。后续每个 stage 完成后，都应按同样格式记录。

## Stage

Stage 0 - Freeze and alignment

## Date

2026-07-08

## Owner

MyPrivateAgent maintainers

## Completed Work

- 明确 MyPrivateAgent 的定位仍是控制面，不向自研执行平台膨胀。
- 固化运行层集成战略，明确成熟框架通过 adapter 接入。
- 生成 OpenSpec change `agent-runtime-plane-integration-strategy`，并完成 proposal / design / specs / tasks。
- 更新入口文档、当前架构、扩展点、roadmap 和 docs 首页。
- 补齐阶段回顾协议和 Stage 1 首切片选择。

## What Stayed Within Scope

- 仅做文档、规格和边界收口。
- 没有把任何外部框架直接接入主执行链。
- 没有把 `AgentHarnessFacade` 推成生产执行层。
- 没有开始自研通用图引擎、checkpoint、sandbox、worker scheduler 或模型网关。

## What Drifted or Got Tempting

- 仓库里已经存在一些运行层实验骨架，容易让人误以为可以直接扩展成生产平台。
- 运行层已有 graph / bootstrap / bridge 代码，容易让执行面和治理面边界变松。

## What Evidence Shows the Stage Is Done

- [运行层集成战略](../architecture/runtime_plane_integration_strategy.md) 已定义四阶段计划和 10 条硬约束。
- [Runtime Plane Stage Review Protocol](./runtime_plane_stage_review_protocol.md) 已可复用。
- [Runtime Plane Stage 1 Slice Selection](./runtime_plane_stage_1_slice_selection.md) 已锁定首切片为 `simple_agent`。
- [Agent Runtime Control Plane Entrypoint](../architecture/agent_runtime_control_plane_entrypoint.md) 与 [Docs 首页](../README.md) 已指向同一方向。

## What Must Not Be Expanded Next

- 不要把运行层实验骨架默认升级成生产执行平台。
- 不要在控制面代码里直接补平台能力。
- 不要跳过 adapter boundary 直接把框架 payload 暴露给治理台。

## Is the Next Stage Still Justified

Yes. 但下一阶段只能是最小 runtime-plane slice，且必须从 `simple_agent` 开始。

## Next Allowed Action

- 在 adapter boundary 下实现 `simple_agent` 的最小执行验证。
- 把 ExecutionRequest / ExecutionEvent / ExecutionResult 的 envelope 跑通。
- 在每个竖切完成后立即写对应 stage review。

## Rollback or Pause Condition

- 运行层工作开始演化成平台克隆。
- 任何实现开始依赖框架私有 payload 作为公共 contract。
- 新增能力不再能清晰回答“它属于 control plane 还是 runtime plane”。
