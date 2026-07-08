# Runtime Plane（运行层面）

## 定位

此目录是 MyPrivateAgent 运行层集成的正式承载位置。

## 职责

| 模块 | 职责 |
|---|---|
| contracts | ExecutionAdapter 标准合同（ExecutionRequest/ExecutionEvent/ExecutionResult） |
| adapters | 外部框架适配器（LangGraph、AgentRun、ADK、OpenAI Agents SDK） |
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
