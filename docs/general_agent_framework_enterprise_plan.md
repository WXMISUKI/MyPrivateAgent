# 通用智能体框架企业级完善总方案

## 1. 文档目的

本文档用于给 `MyPrivateAgent` 当前仓库提供一份可执行的企业级完善总方案，重点回答 4 个问题：

1. 当前项目已经具备哪些框架能力
2. 对照成熟智能体框架，还缺哪些关键能力
3. 后续应该按什么顺序改，才能避免反复返工
4. 每一阶段的交付物、验收标准和风险分别是什么

本文档定位为“总方案”，配套架构稿见：

- [general_agent_framework_target_architecture.md](./general_agent_framework_target_architecture.md)

本文档与现有文档的关系如下：

- [claude_alignment_improvement_plan.md](./claude_alignment_improvement_plan.md)：偏方向收口
- [agent_framework_enterprise_roadmap.md](./agent_framework_enterprise_roadmap.md)：偏阶段路线
- 本文档：偏“基于当前代码现状的正式实施方案”

## 2. 当前项目现状判断

### 2.1 已有基础

当前项目已经超出普通 Demo 范畴，具备较强的通用框架雏形，主要体现在：

- 后端已形成主链路：`AgentHarness -> Orchestrator -> ChatService`
- 已有显式运行时状态与事件协议：
  - `backend/agent_framework/runtime.py`
  - `backend/agent_framework/events.py`
- 已有最小调度与多执行单元雏形：
  - `backend/services/scheduler_service.py`
  - `backend/services/subagent_service.py`
  - `backend/services/subagent_registry_service.py`
- 已有最小治理能力：
  - `backend/services/policy_engine_service.py`
  - `backend/services/agent_hook_service.py`
  - `backend/services/run_trace_service.py`
- 已有能力面和配置面：
  - `backend/services/runtime_surface_service.py`
  - `backend/services/runtime_surface_config_service.py`
- 已有前端治理入口：
  - `PlannerPanel`
  - `RuntimeSurfacePanel`
  - `DoctorPanel`
  - `GovernanceTimelinePanel`
  - `McpManagementPanel`
- 已有后端单测与 CI 骨架，不是零测试项目

### 2.2 核心判断

当前阶段的主要矛盾已经不是“功能不够多”，而是：

- 能力点已经不少，但还没有统一成一套稳定运行时内核
- 调度、子智能体、权限、MCP、记忆、技能之间仍有较多“跨层拼接”
- 治理与观测已经开始形成，但还没有达到企业级可审计、可回放、可分权的程度

换句话说，项目当前最需要的是“统一”和“收口”，而不是继续横向堆功能。

## 3. 参考仓库带来的结论

本次对照参考目录：

- `D:\AI\AIcode\learn-claude-code`
- `D:\AI\AIcode\claude-code`

得到两个很重要的结论。

### 3.1 `learn-claude-code` 的价值

它更适合作为“能力分层检查表”和“演进顺序参考”。

对本项目最有价值的是以下顺序约束：

1. 先有统一 agent loop
2. 再补 tool / planning / subagent / skill / compact
3. 再补 permission / hook / memory / prompt / recovery
4. 再升级为 task / background / scheduler
5. 最后再做 team / worktree / MCP 平台

这意味着你当前项目虽然已经做到了后半程的很多点，但部分能力还需要回到中间层重新“打地基”。

### 3.2 `claude-code` 的价值

它更适合作为“产品化和工程治理参考实现”。

对本项目最值得借鉴的是这些机制：

- 命名子智能体与 fork 子任务的双路径
- worktree 级文件隔离
- 类型化项目记忆与相关性召回
- 技能 frontmatter 元数据和条件激活
- feature flags 与实验能力门控
- 更完整的 hooks、permission、消息标准化与可观测性
- coordinator/worker 的多执行单元编排模式

需要强调的是：本项目不建议盲目追求 CLI/TUI 或表层功能对齐，而是优先吸收这些机制背后的边界设计。

## 4. 当前差距分析

### 4.1 运行时内核差距

已有：

- `AgentState`
- `AgentEvent`
- `run_id`
- planner item trace

不足：

- `run trace` 仍明显依附 planner item，而不是第一类 `Run`
- chat、scheduler、subagent、MCP 之间仍存在“事件转译”而不是“统一原生协议”
- 缺少统一的 `StopReason / ErrorCategory / ApprovalCheckpoint / ArtifactRef`

结论：

- 必须先建立统一运行时协议，否则后续每新增一个能力域都会继续长出新的旁路状态

### 4.2 调度与子智能体差距

已有：

- `scheduler_service` 的 fan-out / collect / merge 雏形
- `subagent_registry` 和角色化 prompt
- 子执行 metadata

不足：

- child execution 仍更像计划项附属结构，不是真正独立运行单元
- 缺少正式的 parent run / child run / background run 模型
- 缺少 worktree 隔离、长任务后台化、恢复与取消策略

结论：

- 调度器应升级为第一类运行时服务，而不是 planner 的增强插件

### 4.3 记忆系统差距

已有：

- `GLOBAL_AGENT.md / PROJECT_AGENT.md / PROJECT_AGENT.local.md`
- `agent_memory_service`

不足：

- 当前更偏“静态层叠指令加载”
- 缺少类型化记忆模型：`user / feedback / project / reference`
- 缺少相关性召回、漂移校验、忽略记忆语义
- 缺少记忆审批、版本、失效与治理机制

结论：

- 记忆系统应从“文件加载器”升级成“受治理的长期上下文系统”

### 4.4 Skill / Command 能力面差距

已有：

- `skill_runtime_service`
- `command_registry_service`
- 前端命令面板和治理页入口

不足：

- command 目前更像 UI 能力目录，尚未成为统一命令协议
- skill 仍偏静态资源与运行时选择，缺少完整 frontmatter 契约
- 缺少 `allowed_tools / effort / model override / context mode / conditional activation`

结论：

- skill 和 command 要升级为框架级协议，而不只是页面功能

### 4.5 策略治理与企业能力差距

已有：

- 最小高风险工具阻断
- 子智能体工具白名单
- run trace 和 capability gap 基础治理

不足：

- 缺少分级授权模型
- 缺少组织、项目、用户三级策略覆盖
- 缺少正式审批单元与审计导出
- 缺少租户隔离和 RBAC 设计

结论：

- 当前治理能力更像“框架自保”，还不是企业级策略平台

### 4.6 工程化差距

已有：

- Python 测试
- Vitest 测试
- CI 基础 jobs
- Ruff 基础配置

不足：

- 根 `pyproject.toml`、`backend/pyproject.toml`、CI Python 版本存在分裂
- 覆盖率门禁较弱
- 前端缺少 lint/typecheck 强约束
- 前后端 API 类型契约未统一
- 结构化日志、指标、追踪、发布质量门禁尚未完全闭环

结论：

- 工程化基础已起步，但还没有达到企业级“长期多人协作可持续演进”的标准

## 5. 总体设计原则

后续改造建议严格遵守以下原则：

### 5.1 统一优先

优先统一协议、状态机、边界和配置源，晚于新增能力点。

### 5.2 运行时优先

优先让 `Run`、`ChildRun`、`Approval`、`Artifact` 成为第一类对象，再谈更多 UI。

### 5.3 治理优先

任何新增能力，必须同时考虑：

- 是否可追踪
- 是否可回放
- 是否可审计
- 是否可分级授权

### 5.4 兼容优先

改造过程中尽量兼容现有 Demo 链路和前端能力面，避免大爆炸式重写。

### 5.5 分阶段交付

每一阶段都必须具备：

- 清晰边界
- 可单独测试
- 可回滚
- 可验收

## 6. 推荐实施阶段

## Phase 0：统一运行时内核

### 目标

把当前分散在 chat、planner、scheduler、subagent、trace 的执行状态，统一为一套正式运行时协议。

### 主要工作项

1. 定义统一 `AgentRun` 模型
2. 定义统一 `ChildRun` 模型
3. 定义统一 `AgentEvent` 扩展字段
4. 统一 `StopReason / ErrorCategory / ApprovalState / ArtifactRef`
5. 将 `run trace` 从 planner item 附属能力升级为 run 原生能力
6. 统一聊天、调度、权限、MCP、技能选择的事件入口

### 交付物

- 新的运行时协议文档
- 运行时状态机实现
- 统一 trace 写入接口
- 兼容旧 API 的适配层
- 后端回归测试

### 验收标准

- 任意一次执行都能按 `run_id` 回放主链路
- planner、subagent、tool、hook、MCP 事件均可挂到同一 `run_id`
- 错误分类和停止原因可统一查询

## Phase 1：调度器与子智能体升级

### 目标

把当前计划项 fan-out 升级成真正的父子执行模型。

### 主要工作项

1. 引入 parent run / child run 生命周期
2. 定义 child run 状态：`queued / running / completed / failed / cancelled`
3. 支持同步子执行与后台子执行
4. 建立 collect / merge 策略抽象
5. 将 scheduler policy 提升为独立策略层
6. 为后续 worktree 隔离预留执行上下文字段

### 交付物

- 新版 `SchedulerService`
- `ChildRunRepository` 或等效持久层
- 调度快照和审计 API
- 角色化 subagent 执行契约

### 验收标准

- 一个 plan item 可以稳定派生多个 child run
- 子执行失败、取消、超时均不会静默丢失
- merge 结果、原始结果、审计轨迹可分别查看

## Phase 2：记忆、技能、命令三层重构

### 目标

把长期上下文与能力入口从“散点功能”收口为统一能力面。

### 主要工作项

1. 设计类型化记忆模型
2. 加入记忆召回与漂移校验
3. 设计 skill frontmatter 契约
4. 支持 skill 的工具白名单、模型覆盖、上下文模式
5. 将 command 升级为统一命令协议
6. 建立 memory / skill / command 的运行时解释链

### 交付物

- `MemoryEntry` 与索引模型
- `SkillDefinition` 契约
- 命令协议与后端执行入口
- 前端 settings / command palette / memory 面升级

### 验收标准

- 运行时可以解释“为什么召回了这条记忆”
- 运行时可以解释“为什么激活了这个 skill”
- 命令不再只是前端跳转动作

## Phase 3：企业级治理与工程基础设施

### 目标

让框架具备企业可接入、可审计、可运维的基础能力。

### 主要工作项

1. 配置分层统一：环境、项目、本地覆写、用户级覆写
2. 引入组织/项目/用户三级策略覆盖
3. 完善审批链、审计导出和整改动作
4. 统一结构化日志、指标、trace
5. 收紧 CI 门禁：lint、test、build、coverage、typecheck
6. 建立 API 契约与版本管理策略

### 交付物

- 配置分层设计
- 审计与策略治理方案
- 质量门禁升级
- 运维指标与告警基础方案

### 验收标准

- 高风险行为具备审批或显式阻断路径
- 多环境配置和本地覆写可解释
- 回归质量门禁可稳定阻止明显退化进入主分支

## Phase 4：操作台与产品化收口

### 目标

把框架内部治理能力转化为可用的操作者工作台。

### 主要工作项

1. scheduler timeline
2. child run 运行视图
3. hook / permission 审计视图
4. MCP 健康与调用视图
5. memory / skill / learning 治理视图

### 验收标准

- 运维与研发无需读原始日志即可理解主要执行链
- 核心治理状态可筛选、聚合、定位

## 7. 建议的第一批实施内容

如果下一轮开始进入代码改造，建议第一批只做以下内容：

1. 统一运行时协议
2. 重构 run trace 归属模型
3. 升级 scheduler 为第一类服务
4. 为 child run 持久化留出模型边界

原因很简单：

- 这是后续所有能力的共同地基
- 不先统一，后面 memory、skill、worktree、审批都会继续旁路生长
- 这批工作能最大程度降低未来返工成本

## 8. 非目标

本阶段不建议优先做以下事情：

- 对齐 `claude-code` 的 CLI/TUI 交互外观
- 一次性做完完整多租户系统
- 接入大量新 provider 或新 MCP server
- 优先扩充前端页面数量
- 在未统一运行时协议前继续增加复杂业务 feature

## 9. 交付建议

建议后续实施采用“文档先行 + 协议先行 + 小步迭代”的方式：

1. 先完成运行时架构稿与数据结构稿
2. 再完成 Phase 0 的代码改造
3. 每阶段完成后补测试、补文档、补 smoke
4. 用 `doctor` 和 `quality gate` 持续做回归守门

## 10. 最终结论

`MyPrivateAgent` 当前最重要的任务不是“继续增加能力”，而是“把已有能力统一成一套企业级智能体运行时底座”。

建议的主线非常明确：

1. 统一运行时内核
2. 升级调度与子智能体模型
3. 重构记忆、技能、命令三层能力面
4. 补齐企业治理与工程基础设施
5. 最后再做产品化操作台收口

只要这条主线不跑偏，这个项目有机会从“能力较多的通用 Agent Demo”稳定演进为“可复用的企业级智能体框架基座”。
