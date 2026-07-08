# Runtime Plane Stage 1 Slice Selection

> 本文记录 Stage 1 的第一个最小运行层切片选择。它不等于实现，只是把“先做什么”先锁住，防止我们一边做一边发散。

## Selection

首个切片建议选择 `simple_agent`。

## Why This Slice First

- 它只需要模型调用，不需要工具、不需要审批、不需要复杂状态分支。
- 它能最快验证执行层与治理层之间的 normalized envelope 是否成立。
- 它最适合作为 adapter-backed runtime 的第一条竖切，不会把团队拖进平台级复杂度。

## What This Slice Must Prove

1. ExecutionRequest 能进入 runtime plane。
2. ExecutionEvent 能回传到 control plane。
3. ExecutionResult 能被治理层消费。
4. 运行层不会把框架原生 payload 直接暴露给治理台。
5. 这个切片不会逼着我们自研 graph engine、checkpoint、sandbox、worker scheduler。

## What This Slice Must Not Become

- 不要在这个切片里加工具调用。
- 不要在这个切片里加审批流程。
- 不要在这个切片里把 `AgentHarnessFacade` 升成生产执行层。
- 不要在这个切片里把 runtime plane 做成一个通用平台。

## After-Stage Review Questions

- 这个切片是否真的只验证了 envelope 和 adapter boundary？
- 是否有任何地方开始依赖框架私有 payload？
- 是否开始顺手补平台能力？
- 下一步是否仍然只是进入 `tool_agent`，而不是跳到更复杂的执行面？

## Next Step After This Slice

如果 `simple_agent` 证明边界成立，下一步才考虑 `tool_agent`，并且仍然必须通过 adapter 进入治理层。
