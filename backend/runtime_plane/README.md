# Runtime Plane（运行层面）

## 定位

此目录是 MyPrivateAgent 运行层集成的正式承载位置。

## 职责

| 模块 | 职责 |
|---|---|
| contracts | ExecutionAdapter 标准合同（ExecutionRequest/ExecutionEvent/ExecutionResult/AgentManifest） |
| adapters | 运行层适配器（当前已落地 `simple_agent` 与 `tool_agent`，后续再扩展外部框架适配） |
| gateway | Intent Router（意图识别路由）、Runtime Selector（运行时选择器） |

## 约束

- 只产出标准事件，不直接写治理 UI
- 框架原生 payload 不得作为外发合同
- 每个 adapter 必须有 promotion gate：experimental → pilot → production
- 不自研通用图引擎、checkpoint、sandbox、worker scheduler

## 当前状态

**实验骨架占位**。目录中的 graph / bootstrap / governance bridge 模块用于收口运行层概念与占位验证，不代表生产级执行平台。
现有 adapter 代码仍在 `backend/agent_framework/framework_adapter_spi/` 中，不搬迁。
新运行层能力应优先放在此目录下，并通过 ExecutionAdapter 合同接入。

## 当前 Stage 1 切片

- `simple_agent`：最小运行层切片，已验证标准 envelope 和 adapter boundary
- `tool_agent`：第二个最小切片，已验证单工具调用闭环和 normalized tool envelope
- 下一步才考虑 `approval_agent`，仍然必须通过 adapter boundary
