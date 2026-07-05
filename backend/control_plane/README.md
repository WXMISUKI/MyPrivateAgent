# Control Plane（治理控制面）

## 定位

此目录是 MyPrivateAgent 治理控制面的正式承载位置。

## 职责

| 模块 | 职责 |
|---|---|
| registry | agent 资产注册与发现（agent.yaml 扫描、能力目录） |
| governance | 治理总览、治理时间线 |
| policy | 策略引擎（工具使用策略、执行策略） |
| approval | 审批流程（创建、决策、回放） |
| trace | 运行追踪（事件流、执行证据） |
| audit | 治理审计（记账、合规） |
| runtime_surface | 运行时表面聚合（contract assembly） |
| contract_gate | 质量门禁（runtime contract checks） |

## 约束

- 只消费标准事件，不理解 LangGraph/AgentRun 私有结构
- 不实现通用执行能力（checkpoint、sandbox、scheduler）
- 新增能力必须先写 OpenSpec

## 当前状态

**骨架占位**。现有代码仍在 `backend/services/` 和 `backend/agent_framework/` 中，不搬迁。
新治理能力应优先放在此目录下。
