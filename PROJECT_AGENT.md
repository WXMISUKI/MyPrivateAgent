# PROJECT_AGENT

## 项目定位

MyPrivateAgent 是企业级 **Agent Runtime Control Plane（智能体运行时治理控制面）**，不是通用智能体框架 demo，也不是 LangGraph / CrewAI / AutoGen / OpenAI Agents SDK / AgentRun 等执行框架的替代实现。

### 我们拥有什么

- **Agent 资产目录**：agent.yaml 注册、能力声明、治理边界
- **运行时契约**：run / event / approval / artifact / trace / audit 等核心对象
- **治理能力**：policy / approval / trace / audit / quality gate / contract gate
- **能力接入层**：Tool / MCP / Skill / Memory / Provider 统一接入
- **交付面**：FastAPI API、Embedded SDK、Vue 治理台、Agent Harness Facade（preview）

### 我们不做什么

- 不自研通用图执行引擎（用 LangGraph）
- 不自研云端沙箱/运行平台（用 AgentRun 或等效）
- 不自研通用 checkpoint / worker scheduler / 模型网关
- 不把外部框架的 raw payload 作为前端治理台的主契约

### 运行层集成战略

外部成熟框架通过 **adapter** 接入，不直接成为主执行路径：

```
Business Frontend / API
  → Intent Router / Gateway
  → Domain Agents (agent.yaml)
  → Execution Plane (LangGraph / AgentRun / ADK)
  → Tools / MCP / RAG / Business Systems
  → MyPrivateAgent Control Plane (policy / approval / trace / audit)
```

详细战略见：[runtime_plane_integration_strategy.md](docs/architecture/runtime_plane_integration_strategy.md)

## 当前重点

- **Stage 0：冻结控制面定位**，停止扩展 harness 执行层
- 明确运行层与治理层的目录边界
- 为 Stage 1（运行层 MVP：simple_agent / tool_agent / approval_agent）做准备

## 10 条开发硬约束

1. 任何新 agent 必须先有 `agent.yaml`，没有 manifest 不允许接运行层
2. 任何运行框架只允许通过 adapter 接入，不允许业务代码直接依赖框架 raw payload
3. MyPrivateAgent 不实现通用 checkpoint、worker scheduler、sandbox、模型网关
4. 高风险工具必须走 policy / approval，不允许 agent prompt 自己声明"我已审批"
5. `runtime_plane/` 只产出标准事件，不直接写治理 UI
6. `control_plane/` 只消费标准事件，不理解 LangGraph/AgentRun 私有结构
7. 新能力必须先写 OpenSpec：目标、非目标、边界、验收、回滚
8. 每个 adapter 必须有 promotion gate：experimental → pilot → production
9. 每个 agent 必须有最小 eval 或 smoke，不要求复杂，但必须能证明没有越界
10. 禁止"顺手扩展平台能力"：发现缺口先记录，不在业务迁移中顺手补平台

## 在回答用户时

- 先按当前已注册能力判断是否可完成
- 若需求超出能力范围，要明确指出缺口属于工具、Skill 还是 MCP capability
- 优先帮助开发者识别"后续应补哪类能力"，而不是硬凑看似完整的结果
- 当用户问到执行层能力（图编排、循环、多智能体协作）时，应引导到 LangGraph/AgentRun 而不是自研
