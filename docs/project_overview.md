# MyPrivateAgent 项目全景文档

> 这份文档的目标：让任何第一次接触本项目的人，在 30 分钟内建立关于"它是什么、做到哪一步、哪些能力真正跑通、哪些还在路上"的准确认知。面向对象是自己、技术面试官、以及想快速评估项目成熟度的合作者。

## 1. 项目一句话定位

`MyPrivateAgent` 是一个**参考 Claude Code 架构自研的通用智能体运行时框架**，目标不是做一款特定垂域的 Agent 产品，而是为后续任意垂域（客服、代码、天气、知识助手等）Agent 提供一个**可复用的运行时底座**：主链路、调度器、工具/Skill/MCP 三层能力面、记忆、权限治理、可观测性全部自研并已收口。

当前状态定位：

- **不是** demo chatbot 级别的玩具
- **不是** 直接包一层 LangChain/LangGraph 就交付的壳子
- **是** 一个已经有明确运行时协议（`AgentRun / AgentEvent / ChildRun`）、经过多轮架构收敛、具备企业级演进路线的通用智能体框架

## 2. 技术栈一览

| 层 | 选型 |
|---|---|
| 后端框架 | FastAPI 0.115 + SQLAlchemy 2.0 + Alembic |
| 鉴权 | JWT (python-jose) + bcrypt + `demo_guest` 免登录模式 |
| LLM 编排 | LangChain 0.3 / LangGraph 0.2 （仅在 tool binding / message 形态层使用，核心循环自研） |
| 模型 Provider | 火山引擎豆包 Ark（OpenAI 兼容）、Ollama 本地模型，已预留 Anthropic / OpenAI 抽象 |
| 前端 | Vue 3.4 + Vite 5 + Pinia + Vue Router 4 |
| 测试 | Python unittest + pytest + pytest-cov、前端 Vitest + @vue/test-utils |
| 质量门禁 | ruff 0.4.4、quality_gate_report.py、多个 smoke 脚本 |
| 部署 | Vercel 一体化（Vue SPA + FastAPI serverless 函数）、Dockerfile 可独立部署 |
| 存储 | 默认本地 SQLite (`.myagent/app.db`)，可无缝切 MySQL |

代码规模（截至 2026-05）：

- 后端 Python：约 21K 行，其中 `backend/services` 下 40+ 个领域服务约 12K 行
- 前端 Vue：约 13K 行，含 14 个业务组件、7 个主视图
- 测试：约 8K 行，覆盖 40+ 个服务的单测与 smoke
- 文档：`docs/` 下 20+ 份设计稿、路线图、运维手册

## 3. 分层架构

项目在 `docs/general_agent_framework_target_architecture.md` 中已经显式规划并落地为六层：

```
+--------------------------------------------------------------+
| Interface Layer                                              |
| FastAPI Routers / Vue SPA / Card Schemas / SSE              |
+--------------------------------------------------------------+
| Orchestration Layer                                          |
| ChatService / PlannerService / CommandRegistry               |
+--------------------------------------------------------------+
| Runtime Core Layer                                           |
| AgentHarness (loop) / AgentRunContext / EventFactory /       |
| Scheduler / Subagent                                         |
+--------------------------------------------------------------+
| Governance Layer                                             |
| PolicyEngine / PermissionService / AgentHook / RunTrace /    |
| Doctor / QualityGate / CapabilityGap                         |
+--------------------------------------------------------------+
| Capability Layer                                             |
| ToolRuntime / SkillRuntime / McpRuntime / MemoryRuntime      |
+--------------------------------------------------------------+
| Infrastructure Layer                                         |
| SQLAlchemy / Alembic / Logging / Config / .myagent store     |
+--------------------------------------------------------------+
```

这套分层不是文档上的示意图，是代码里真实存在的目录边界：

- `backend/agent_framework/` 运行时一等对象：`AgentState / AgentRunKind / AgentEvent / ArtifactRef`
- `backend/harness/` 主执行循环：`AgentHarness`、`ToolRegistry`、`ContextManager`、`MemoryManager`、`PermissionService`
- `backend/orchestrator.py` 主协调器入口（简化版 `SimplifiedOrchestrator`）
- `backend/services/` 领域服务（近 40 个），按域组织：planner、scheduler、subagent、policy、mcp、skill、memory、capability、feedback、provider、runtime surface、trace、hook、compaction、doctor
- `backend/routers/` FastAPI 路由入口
- `backend/agent_server/` 可配置的 app 工厂（支持 `full_stack / chat_only / admin_only` 等 preset）
- `backend/alembic/` 数据库迁移，已有 3 个版本（`scheduler_runtime_tables / permission_runtime_scope / runtime_activity_tables`）

## 4. 核心执行链（最值得讲清楚的一条主线）

一次用户消息的生命周期，从路由到事件流，完整链路是：

```
HTTP POST /api/chat
   └─▶ routers/chat.py
         └─▶ ChatService (services/chat_service.py)
               ├─▶ PlannerService（可选：识别是否需要计划）
               ├─▶ PolicyEngineService（前置策略判定）
               ├─▶ SchedulerService（如存在 fan-out 需求）
               └─▶ SimplifiedOrchestrator
                     └─▶ AgentHarness.run(messages)   ← 核心循环
                           │
                           │ 每轮迭代：
                           │  1. AgentRunContext.begin_iteration()
                           │  2. 触发状态迁移事件（state transition）
                           │  3. 拼装 system prompt：
                           │     - Agent Identity
                           │     - Capability Profile
                           │     - GLOBAL_AGENT.md / PROJECT_AGENT.md 分层记忆
                           │     - Skill Runtime 匹配结果
                           │     - MCP 能力目录
                           │  4. LLM 流式调用（bind_tools + streaming）
                           │  5. StreamingToolCallTracker 聚合分块参数
                           │  6. PermissionService 判定是否需要审批
                           │  7. 工具执行 / 结果入 trace
                           │  8. CompletionEvaluator 判定是否可终止
                           │  9. AgentHook PreToolUse / PostToolUse
                           │ 10. 错误分类 + 指数退避 + provider fallback
                           │
                           └─▶ SSE 向前端推送 AgentEvent 流
```

**每一次执行都有统一的 `run_id`、可回放的事件流、完整的状态机轨迹。** 这是项目最重要的架构资产。

### 4.1 状态机（落地于 `backend/agent_framework/runtime.py`）

```
INIT → PLANNING → GENERATING → TOOL_CALLING
                              → WAITING_APPROVAL
                              → WAITING_PERMISSION
                              → OBSERVING → MERGING → FINALIZING → DONE
                                                                  → FAILED
                                                                  → ABORTED
```

状态迁移表 `_STATE_TRANSITIONS` 在代码中是显式白名单，**非法迁移直接抛 ValueError**，避免状态机被运行时代码悄悄污染。

### 4.2 事件协议（`backend/agent_framework/events.py`）

统一事件结构：`event_id / run_id / parent_run_id / conversation_id / iteration / type / payload`。

事件类型：`state / status / reasoning / content / tool_call_start / tool_result / tool_permission_required / tool_denied / plan_updated / done / error`。

所有事件都可按 `run_id` 串起主链路，按 `parent_run_id` 串起父子链路。

### 4.3 一等对象已持久化

`backend/models.py` 中已有正式的数据库表：

- `PlanRunRecord / PlanItemRecord` — 计划域
- `SchedulerRunRecord / ChildRunRecord` — 调度域（child run 已从 metadata 升级为一等表）
- `BackgroundRunRecord / WorktreeRunRecord` — 后台执行、worktree 隔离预留
- `PermissionRequestRecord` — 权限/审批请求
- `ArtifactRecord` — 统一工件
- `CapabilityRemediationRecord` — 能力缺口与整改建议
- `MessageFeedbackRecord` — 幂等反馈（含 `uq_message_feedback_conv_msg_user` 唯一约束）
- `Learning / LearningReviewRecord / LearningVersionRecord` — 学习治理与版本

这意味着项目已经完成了从"运行时只是 metadata 拼接"到"运行时是第一类持久对象"的演进，这是企业级改造路线图 Phase 0 的核心验收项。

## 5. 七个核心子系统

### 5.1 AgentHarness — 自研的核心循环

位于 `backend/harness/agent_harness.py`，约 1800 行。关键能力：

- **流式工具调用聚合**：豆包等 OpenAI 兼容模型在流式返回工具调用时会按 `index` 分块，`StreamingToolCallTracker` 负责按 index 聚合参数、去重片段、容错解析 JSON（含 `json_repair` 兜底）
- **bind_tools 双模**：支持 LangChain `bind_tools` + 豆包原生工具定义格式，检测到"模型不支持工具"时自动降级为纯文本解析
- **错误分类与指数退避**：`ErrorHandler` 把底层异常归一到 `provider_timeout / provider_connection / provider_rate_limit / provider_unavailable / tool_validation` 五类，可重试的走指数退避（最大 60s）
- **迭代预算**：`max_iterations=10`，配合 `CompletionEvaluator` 决定是否终止
- **相似工具调用防抖**：`max_similar_tool_calls=2`，避免模型陷入同一工具重复调用循环
- **最终合成模式**：在已积累足够中间结果后，切回未 bind_tools 的原始模型做最终答复合成

### 5.2 Scheduler + Subagent — 真正的父子执行模型

- `SchedulerService`（`backend/services/scheduler_service.py`）负责把一个 planner item fan-out 成多个 child run，child 状态为 `queued / running / completed / failed / cancelled`
- `SubagentRegistryService` 持有角色化配置：`frontend / backend / qa / docs / planner`，每个角色有自己的工具白名单、提示词指令
- `SubagentContext` 是正式的运行时上下文对象，显式承载 `run_id / parent_run_id / agent_role / execution_mode / required_capabilities`
- `ChildRunRecord` 表已把 child run 升级为数据库一等对象，不再依赖 planner metadata
- 有配套 smoke：`scripts/multi_agent_policy_smoke.py`、`scripts/multi_agent_provider_failover_smoke.py`

### 5.3 PolicyEngine + PermissionService — 最小治理闭环

- `PolicyEngineService` 做确定性前置判定，支持三类规则：
  - 高风险工具关键字阻断（`filesystem_write / delete / remove / payment / booking`）
  - 子智能体工具白名单
  - Provider 优先级顺序（`volcengine-ark → anthropic → openai`）
- `PermissionService` 负责运行时审批请求持久化、超时兜底、状态转移。在 `WAITING_PERMISSION` 状态暂停执行，审批结果通过 SSE 回推
- `AgentHookService` 提供 `PreToolUse / PostToolUse / SessionStart / Stop` 生命周期钩子，治理事件统一落 run trace

### 5.4 三层能力面：Tool / Skill / MCP

- **Tool**：`ToolRegistry` 统一注册、`ToolSpec` 包含 permission_level、deterministic、cache TTL、render mode、card_schema；已接入 weather、datetime、search、LangChain 工具
- **Skill**：`SkillRuntimeService` 负责按 frontmatter 匹配、按 trigger 词命中、按 agent role 过滤；Skill 有 `activation_mode / priority / required_capabilities / agent_roles / tags`
- **MCP**：`McpRegistryService + McpRuntimeService + McpSessionService + McpAdapterService` 四件套，覆盖注册、握手、tools/call、session 管理、capability 路由。支持 stdio / http 两种 transport

三层能力面在每轮执行前由 `CapabilityProfileService` 合成为运行时能力合同，明确告诉模型：**哪些能力可用、哪些受限、哪些完全缺失。**

### 5.5 分层记忆 + Capability Gap

- **静态记忆**：`GLOBAL_AGENT.md`（角色宣告）+ `PROJECT_AGENT.md`（项目规则）+ `PROJECT_AGENT.local.md`（本地覆写），由 `MemoryManager` 按层叠加
- **Agent Memory 服务**：`AgentMemoryService` 提供运行时可写入的长期记忆条目（当前结构仍偏"静态加载"，类型化记忆在 roadmap 中）
- **能力缺口观测**：每次触发能力边界降级都写入 run trace，`CapabilityGapService` 聚合近期高频缺失能力，输出建议补强方向（工具 / Skill / MCP）

### 5.6 Provider 抽象 + 自动故障转移

- `ProviderConfigService` 持久化 provider 配置，支持 Ark、Ollama、以及未来的 Anthropic/OpenAI
- `ProviderFailoverAnalyticsService` 统计 provider 失败率、降级触发次数，为 policy engine 的 provider 顺序选择提供依据
- `/api/runtime-profile` 读取、`PATCH` 持久化运行时安全配置（`auth_mode / default_model`）

### 5.7 可观测性：RunTrace + Doctor + QualityGate

- **RunTrace**：统一 trace 入口，chat / scheduler / subagent / policy / hook / mcp 都落到同一张表，按 `run_id / parent_run_id` 可回放
- **Doctor**：`scripts/doctor.py` + `DoctorRuntimeService` 做 `.env`、数据库、前端构建产物、模型配置的自检
- **QualityGate**：`scripts/quality_gate_report.py` 聚合最近 14 天的 open actions、long-blocked actions，产出 `quality-gate-report.json` + markdown summary，CI 中作为 job 并 upload artifact

## 6. 前端治理面板

`frontend-vue` 不是传统的"只会聊天的 UI"，而是一个包含治理能力的操作台：

| 面板 | 作用 |
|---|---|
| `ChatView` | 主聊天界面，支持 SSE 流式输出、工具调用卡片、中断生成、反馈打分 |
| `AgentRuntimeDebugPanel` | 实时显示当前 run 的状态机、事件流、工具历史 |
| `PlannerPanel` | 计划项管理、child run 追踪、merge summary |
| `RuntimeSurfacePanel` | 运行时能力面板（auth_mode / default_model / provider / model 目录） |
| `DoctorPanel` | Doctor 自检结果展示 |
| `GovernanceTimelinePanel` | 权限、策略、审批的治理时间线 |
| `McpManagementPanel` | MCP 服务器注册、健康探测、能力目录 |
| `ProviderConfigPanel` | Provider 配置、降级统计 |
| `CapabilityGapSummaryPanel` | 能力缺口聚合视图 |
| `CommandPalette` | 命令面板，统一触发治理动作 |
| `SettingsView / SkillsView / LearningsView / FeedbackAnalyticsView` | 设置、技能治理、学习治理、反馈分析 |

结构化卡片：`AgentStructuredCard / WeatherCard / DateTimeCard / SearchSummaryCard`，走统一 card schema 协议（`docs/agent_framework_card_schemas.md`），后端工具可声明 `card_schema`，前端按 schema 渲染。

## 7. 工程化与质量门禁

### 7.1 CI（`.github/workflows/ci.yml`）

四个 job：

1. `backend-lint`：ruff check
2. `backend-tests`：显式列出 28 个核心测试模块跑 unittest，额外跑一轮 pytest + coverage（阈值 30%）
3. `quality-gate`：生成 quality gate 报告并 upload artifact，有阈值检查（`max-open-actions=10`、`max-long-blocked-actions=0`）
4. `frontend-build`：npm run build 验证生产包可构建

### 7.2 Smoke 脚本（`backend/scripts/`）

- `doctor.py` / `smoke_check.py` — 环境与路由自检
- `auth_session_smoke.py` — 认证与会话主链路
- `chat_stream_smoke.py` — SSE 流式主链路
- `chat_empty_response_smoke.py` — 上游空响应兜底
- `chat_error_event_smoke.py` — 流式错误事件
- `chat_stop_generation_smoke.py` — 停止生成合约
- `multi_agent_policy_smoke.py` — 多智能体策略
- `multi_agent_provider_failover_smoke.py` — provider 降级
- `capability_gap_governance_smoke.py` — 能力缺口治理
- `quality_gate_smoke.ps1` — 质量门禁冒烟（Windows）
- `dedupe_message_feedback.py` — 反馈数据治理（含 dry-run）

### 7.3 部署

- **Vercel 一体化**（`vercel.json`）：前端 dist 做静态路由，`/api/*` 走 `api/index.py` serverless
- **Dockerfile**：基于 `python:3.11-slim`，直接运行 `uvicorn main:app`
- **数据库**：默认 SQLite 本地零配置，`DB_MODE=mysql` 即可切 MySQL，已有 `alembic` 迁移

## 8. 文档与设计稿

`docs/` 下不是"一篇 README 糊弄事"的状态，按决策链组织：

- **总方案 & 目标架构**
  - `general_agent_framework_enterprise_plan.md`
  - `general_agent_framework_target_architecture.md`
- **路线图与阶段方案**
  - `agent_framework_enterprise_roadmap.md`
  - `framework_execution_roadmap.md`
  - `claude_alignment_improvement_plan.md`
- **子域方案**
  - `planner_todo_framework_plan.md`
  - `mcp_registry_framework_plan.md`
  - `skill_runtime_framework_plan.md`
  - `feedback_learning_governance_plan.md`
  - `demo_storage_architecture_plan.md`
- **协议与接入**
  - `agent_framework_card_schemas.md`
  - `agent_framework_starter_guide.md`
  - `agent_framework_demo_guide.md`
- **运维与测试**
  - `demo_runbook.md`
  - `test_manual.md`
  - `failover_alert_observability_guide.md`
  - `online-deployment-cors-fix-guide.md`
  - `v0_freeze_acceptance_report_template.md`

这套文档结构本身就是"文档先行 + 协议先行 + 小步迭代"方法论的证据。

## 9. 当前成熟度判断

对照 `general_agent_framework_enterprise_plan.md` 的五个阶段：

| 阶段 | 状态 | 说明 |
|---|---|---|
| Phase 0 统一运行时内核 | 主体完成 | `AgentRun / AgentEvent / 状态机 / RunTrace` 已落地为代码 |
| Phase 1 调度器 + 子智能体 | 主体完成 | `ChildRunRecord` 已一等化，fan-out / collect / merge 走通，subagent 角色注册、工具白名单、provider 降级闭环 |
| Phase 2 记忆 / 技能 / 命令 | 部分完成 | Skill frontmatter 契约、command 面板、分层记忆都已落地；**类型化记忆、记忆召回漂移校验尚缺** |
| Phase 3 企业级治理与工程 | 部分完成 | policy engine、permission、hook、doctor、quality gate 都有；**组织/项目/用户三级策略、审批链、正式审计导出尚缺** |
| Phase 4 产品化操作台收口 | 主体完成 | 前端治理面板已齐全，但内部运维可用度还需打磨 |

**简单说：Phase 0/1/4 主体完成，Phase 2/3 做到了一半。**

## 10. 可以直接跑通的主链路

对面试官或合作者演示的最短路径：

```powershell
# 1. 后端
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/doctor.py            # 自检
python -m uvicorn main:app --reload --port 8000

# 2. 前端
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm install && npm run dev

# 3. 浏览器打开 http://localhost:5173
#    - demo_guest 模式自动进入聊天
#    - 问一句"上海今天天气"会走 weather tool，前端按 card schema 渲染
#    - 在 Settings / PlannerPanel / DoctorPanel 里能直接看到运行时治理面
```

或者直接跑 smoke，一条命令覆盖认证 + 会话 + SSE：

```powershell
python scripts/chat_stream_smoke.py
```

## 11. 项目的风险与已知债务

务实地讲，这个项目有以下**真实存在**的债务（HR/面试场景主动说清楚反而加分）：

1. **类型化记忆还没落地**：目前 `AgentMemoryService` 仍偏"文件 + 条目"的加载层，缺 `user / feedback / project / reference` 四类语义，也没有相关性召回评分、漂移校验
2. **权限模型偏单层**：还没有组织 / 项目 / 用户三级策略覆盖，`ApprovalEngine` 作为独立一等对象只是规划，当前走 `PermissionRequestRecord` 走通了最小闭环
3. **测试覆盖阈值偏低**：CI 里 `--cov-fail-under=30`，真实需要提升到 60%+ 才配得上"企业级"
4. **前端缺少 lint / typecheck 强约束**：Vue 侧没有 TS 化，没有 pre-commit hook，`npm run lint` 只是 eslint --fix
5. **API 契约未用 pydantic → OpenAPI → 前端类型**闭环：`schemas.py` 已显式定义，但前端仍手写 JS 调用
6. **worktree 隔离是数据库表占位**：`WorktreeRunRecord` 存在，但实际 git worktree 操作尚未接入
7. **Python 版本与构建基线有碎片**：根 `pyproject.toml`、`backend/pyproject.toml`、CI 的 Python 版本还没完全统一（3.11 为主）
8. **MCP 仍偏 registry + 短连接**：长连接 session 复用、audit trail 还在完善

这些都在 `docs/general_agent_framework_enterprise_plan.md` 有明确记录和后续计划。

## 12. 一句话总结

> 这是一个用"协议先行、文档先行、小步迭代"方式，在本地从零构建的通用智能体运行时框架。它不是业务应用，是**下一个业务智能体要坐上去的那把椅子**。已经能演示完整执行链，具备可观测、可治理、可审批、可回放的最小闭环。
