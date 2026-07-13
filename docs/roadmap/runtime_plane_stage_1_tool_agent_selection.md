# Runtime Plane Stage 1 Slice Selection - Tool Agent

> 本文记录 Stage 1 的第二个最小运行层切片选择。它不等于完整工具平台，只是把“一个受控工具闭环”先锁住，避免我们直接滑向审批、多工具编排或框架平台化扩张。

## Selection

首个 tool slice 选择 `tool_agent`。

## Why This Slice Now

- 它只比 `simple_agent` 多一层受控工具调用，不需要审批、不需要多智能体。
- 它能验证 tool schema、tool result、tool observation 和 normalized envelope 是否还能保持稳定。
- 它最适合作为 runtime-plane 从“会跑”迈向“会跑一个工具”的最小竖切。

## What This Slice Must Prove

1. `ExecutionRequest` 仍然能进入 runtime plane。
2. 工具调用能被执行并回传为标准化事件。
3. `ExecutionResult.tool_calls` 可以被治理层消费。
4. 框架原生 tool payload 不会直接暴露给治理台。
5. 这个切片不会逼着我们自研更大的工具平台或审批平台。

## What This Slice Must Not Become

- 不要在这个切片里加审批流程。
- 不要在这个切片里加多智能体路由。
- 不要把 `tool_agent` 直接变成通用工具编排器。
- 不要把 runtime plane 做成一个新平台。

## Next Allowed Action

如果 `tool_agent` 证明边界成立，下一步才考虑 `approval_agent`，并且仍然必须通过 adapter 进入治理层。
