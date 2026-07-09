# Runtime Plane Archive Notes

> 这是 `agent-runtime-plane-integration-strategy` 这次变更的收尾说明。它不新增能力，只把已确认的边界、阶段回顾和下一步许可动作压实，避免后续开发把控制面再次拖向平台膨胀。

## Freeze Decision

- MyPrivateAgent 保持 `Agent Runtime Control Plane` 定位，不自建通用执行平台。
- 运行层只通过成熟框架和 adapter 进入，不把框架原生对象暴露给治理合同。
- `AgentHarnessFacade` 维持 preview/local smoke 边界，不向生产执行层扩展。

## Adapter Boundary

- 对外公开的运行合同以 `ExecutionRequest`、`ExecutionEvent`、`ExecutionResult`、`AgentManifest` 为准。
- 框架内部 payload、provider client、stream iterator、checkpoint 细节都只能留在 adapter / runtime 私有边界内。
- 任意新运行能力先写 OpenSpec，再决定是否进入 `backend/runtime_plane/` 或 `backend/framework_adapters/`。

## Stage Reviews

- [Stage 0 Review](./runtime_plane_stage_0_review.md)：完成冻结与定位收口。
- [Stage 1 Slice Review](./runtime_plane_stage_1_simple_agent_review.md)：完成 `simple_agent` 最小 envelope 竖切。
- [Stage Review Protocol](./runtime_plane_stage_review_protocol.md)：后续每个 stage 必须继续按同一模板回顾。

## Next Allowed Action

- 下一步只允许进入更小的 runtime-plane slice 或 adapter promotion review。
- 如果要扩展 `tool_agent`、`approval_agent` 或新的外部框架 adapter，必须先补 OpenSpec，再做最小竖切。
- 如果实现开始向 checkpoint、sandbox、worker scheduler、通用图引擎膨胀，必须回到 freeze-and-align 重新收口。

## Current Outcome

- 方向已固定。
- 边界已明确。
- 首个 runtime-plane slice 已打通。
- 后续推进必须是受约束的增量，而不是平台化扩张。
