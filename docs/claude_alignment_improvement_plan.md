# 通用智能体框架对齐 Claude Code 的完善方案

本文档用于记录 `MyPrivateAgent` 作为通用智能体框架 demo，继续向 Claude Code 一类成熟智能体靠拢时的重点完善方向。目标不是补单点业务工具，而是补齐底座级能力，方便后续快速承载垂域智能体。

## 当前判断

项目已经从“能跑 demo”进入“具备治理意识的 Agent 基座”阶段，已有基础包括：

- 主智能体身份与能力边界
- 复合任务执行闭环
- 工具调用与单次补查
- 能力缺口反馈
- runtime surface 雏形
- demo_guest 运行模式
- 治理统计第一层

但距离 Claude Code 一类成熟智能体，还存在以下关键差距：

- 缺少真正的分层记忆 / 指令系统
- 缺少正式的 subagent 注册与权限面
- 缺少 hooks / permission 治理层
- 缺少工作流命令层
- 缺少 provider / model 质量治理
- 缺少系统性评测与回归基线

## 六条主线

### 1. 分层记忆与指令系统

目标：把主智能体行为从“代码里写死的 prompt”升级为“框架级身份 + 项目级规则 + 本地级偏好 + 运行时能力面”的组合。

建议分层：

- `GLOBAL_AGENT.md`
  - 通用底座级规则
- `PROJECT_AGENT.md`
  - 项目共享规则
- `PROJECT_AGENT.local.md`
  - 本地实验规则
- `ORG_POLICY.md`
  - 后续预留企业策略位

### 2. Subagent 正式能力面

目标：把当前偏调度单元的 subagent，升级成可治理的角色化子智能体。

建议注册字段：

- `name`
- `description`
- `allowed_tools`
- `preferred_models`
- `context_policy`
- `trigger_conditions`

建议先落三类通用子智能体：

- `researcher`
- `planner`
- `executor`

### 3. Hooks / Permission 治理层

目标：把工具调用和关键执行阶段纳入统一治理。

建议最小事件面：

- `PreToolUse`
- `PostToolUse`
- `OnFallback`
- `OnSubagentSpawn`
- `OnFinalSynthesis`

### 4. Workflow / Slash Command 层

目标：把高频框架操作沉淀成稳定命令层，而不是每次靠自然语言触发。

建议优先支持：

- `/runtime`
- `/capabilities`
- `/plan`
- `/doctor`
- `/gaps`
- `/model`
- `/permissions`

### 5. Provider / Model 质量治理

目标：不只是能切模型，而是知道哪个 provider / model 更适合哪类复合任务。

建议统计：

- 首 token 时间
- completion timeout 次数
- fallback 触发率
- tool failure rate

### 6. 评测与回归基线

目标：让框架演进可控，而不是每次修改后靠人工感觉判断。

建议覆盖：

- 纯工具请求
- 复合任务
- 能力不足场景
- provider 异常场景

## 实施顺序

### P0

1. 分层记忆 / 指令系统
2. Subagent 注册与权限面
3. Hooks 基础框架

### P1

1. Workflow / Slash Command 层
2. Provider / Model 质量治理

### P2

1. 评测与回归基线
2. 治理台与统计面板继续增强

## 本轮落地范围

本轮先做：

1. 方案文档入库
2. 分层记忆 / 指令系统最小闭环
3. 将记忆层加载状态接入运行时能力面

后续按 [framework_execution_roadmap.md](./framework_execution_roadmap.md) 与本文档并行推进：前者负责现有框架演进里程碑，本文档负责与 Claude Code 对齐的能力方向。
