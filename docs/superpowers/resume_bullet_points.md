# MyPrivateAgent 技术简历段落（可直接复用）

> 这份文档提供多个长度、不同侧重的简历段落，可按目标岗位（AI 应用工程师 / 全栈 / 平台工程 / 后端架构）挑选复用。所有数字和技术点都有对应代码位置可核验，不吹不夸。

---

## 版本 A：标准版（推荐，适合大多数 AI / 全栈岗位）

### MyPrivateAgent — 通用智能体运行时框架（个人项目，Python / Vue 3）

> 参考 Anthropic Claude Code 架构自研的通用智能体运行时底座，为后续任意垂域 Agent 提供可复用的主链路、调度器、治理层与能力面。**非业务应用，是框架基座**。代码规模：后端 21K 行 / 前端 13K 行 / 测试 8K 行 / 设计文档 20+ 份。

- **自研 AgentHarness 核心循环**（1,800 行）：实现流式工具调用按 index 分块聚合、`bind_tools` / 豆包原生双模自动降级、错误分类 5 类 + 指数退避重试、相似工具调用防抖、最终合成模式切换
- **落地运行时一等对象协议**：`AgentRun / AgentEvent / ChildRun / ArtifactRef` 通过 SQLAlchemy 持久化（20+ 张表、3 个 Alembic 迁移版本），显式状态机 11 个状态 + 白名单迁移表，非法迁移直接抛错，任意执行可按 run_id 完整回放
- **真正的父子执行模型**：planner item fan-out 多个 child run，子智能体按 `frontend / backend / qa / docs / planner` 角色注册与工具白名单，provider 失败自动降级并落 failover analytics
- **三层能力面 + 运行时能力合同**：Tool 层 `ToolSpec` 元数据、Skill 层 frontmatter 契约与触发匹配、MCP 四件套（Registry / Runtime / Session / Adapter，支持 stdio / http），每轮执行合成能力合同写入 system prompt
- **治理闭环**：`PolicyEngine` 确定性前置判定、`PermissionService` 审批持久化、`AgentHook` 生命周期钩子、`RunTrace` 统一追踪、`Doctor` 环境自检、`CapabilityGap` 缺口聚合与补强建议
- **前端操作台**：Vue 3 + Pinia + Vite 实现 10+ 治理面板（Runtime Debug / Planner / Governance Timeline / MCP / Provider / Capability Gap / Command Palette），SSE 流式渲染，结构化卡片协议（`card_schema`）
- **工程化**：GitHub Actions 四 Job 流水线（ruff / unittest+coverage / quality-gate / frontend-build），40+ 后端单测、10+ smoke 脚本（认证 / SSE / 错误事件 / 停止生成 / 多智能体策略 / provider 降级 / 能力缺口治理），Vercel 一体化部署 + Dockerfile 独立部署双路径
- **方法论**：以"协议先行、文档先行、小步迭代"推进，`docs/` 下维护总方案、目标架构、路线图、子域方案、验收清单，每次架构收敛都留下设计稿与演进记录

**技术栈**：Python 3.11 / FastAPI / SQLAlchemy / Alembic / LangChain / LangGraph / Pydantic / Vue 3 / Pinia / Vite / Vitest / pytest / ruff / SSE / JWT / Vercel / Docker

---

## 版本 B：精简版（3 条 bullet，适合简历空间紧张）

### MyPrivateAgent — 通用智能体运行时框架（个人项目）

- 参考 Claude Code 架构自研 42K+ 行全栈智能体框架基座，落地运行时一等对象协议（`AgentRun / AgentEvent / ChildRun`）+ 显式状态机 + 统一事件流，任意执行可按 run_id 回放
- 实现父子执行模型、三层能力面（Tool / Skill / MCP）、治理闭环（Policy / Permission / Hook / RunTrace / Doctor / QualityGate），自研 AgentHarness 核心循环含流式工具调用聚合、错误分类、provider 自动降级
- 前端 Vue 3 实现 10+ 治理面板与结构化卡片协议，GitHub Actions 四 Job 流水线（lint/tests/quality-gate/build），40+ 单测 + 10+ smoke 脚本，支持 Vercel 一体化与 Docker 双部署路径

---

## 版本 C：后端架构侧重版（适合平台 / 架构岗）

### MyPrivateAgent — 通用智能体运行时底座（个人项目，FastAPI + SQLAlchemy）

- **主链路架构**：设计六层分层（Interface / Orchestration / Runtime Core / Governance / Capability / Infrastructure），通过 `AgentHarness → Orchestrator → ChatService` 主链路收口执行控制流，替换散点式的 chat-route 逻辑
- **运行时协议设计**：把 `AgentRun / AgentEvent / ChildRun / ArtifactRef / PermissionRequest` 从 metadata 拼接升级为数据库一等对象（20+ 张表、3 个 Alembic 迁移），状态机通过白名单迁移表 + 显式 ValueError 保证 invariant
- **多智能体调度**：`SchedulerService` 支持 `fan-out → collect → merge`，child run 独立状态 `queued / running / completed / failed / cancelled`，与父 run 通过 `parent_run_id` 关联
- **治理架构**：`PolicyEngineService` 确定性前置判定（高风险工具阻断、工具白名单、provider 优先级）、`PermissionService` 把审批从状态耦合中剥离为独立持久化对象、`RunTraceService` 统一 chat / scheduler / subagent / policy / hook / mcp 的 trace 入口
- **可观测性**：SSE 统一事件协议（`event_id / run_id / parent_run_id / iteration / type / payload`），前后端兼容的 payload 扁平化设计，`quality_gate_report.py` 聚合 14 天治理数据并在 CI 中 upload artifact
- **可靠性工程**：错误分类 5 类 + 指数退避（最大 60s）、provider 自动故障转移 + analytics、`CapabilityGapService` 识别高频缺失能力并输出补强方向、`Doctor` 启动自检覆盖 `.env` / 数据库 / 关键目录 / 构建产物 / provider 配置
- **工程化**：ruff + pytest-cov + unittest 显式模块列表 + 10+ smoke 脚本组成 CI 四 Job 流水线；SQLite / MySQL / 内存三模式通过配置切换（Vercel 环境自动识别）

**技术栈**：Python 3.11 / FastAPI / SQLAlchemy 2.0 / Alembic / Pydantic 2 / LangChain / LangGraph / SSE / JWT / Slowapi / ruff / pytest

---

## 版本 D：全栈 / 前端侧重版

### MyPrivateAgent — 通用智能体框架（个人项目，FastAPI + Vue 3）

- **前端操作台**：Vue 3.4 + Pinia + Vue Router 4 + Vite 5，实现 10+ 治理面板：`AgentRuntimeDebugPanel`（状态机 / 事件流）、`PlannerPanel`（child run 追踪）、`GovernanceTimelinePanel`（权限审批时间线）、`McpManagementPanel`、`RuntimeSurfacePanel`、`CapabilityGapSummaryPanel`、`CommandPalette` 等
- **SSE 流式渲染**：ChatView 按 AgentEvent type 分发渲染（`content / tool_call_start / tool_result / state / error / done`），工具结果走**结构化卡片协议**（统一 `card_schema`），已实现 `WeatherCard / DateTimeCard / SearchSummaryCard / AgentStructuredCard` 四类
- **反馈闭环**：消息级反馈打分 + runtime effect 关联 + analytics view，数据库侧通过 `uq_message_feedback_conv_msg_user` 唯一约束保证幂等
- **后端全栈**：FastAPI + SQLAlchemy 2.0，自研 AgentHarness 核心循环（1.8K 行），父子执行模型、策略引擎、权限服务、RunTrace、三层能力面全部落地
- **部署工程**：Vercel 一体化（Vue dist 静态路由 + `/api/*` Python serverless）与 Dockerfile 双部署路径，GitHub Actions 四 Job 流水线（lint / tests / quality-gate / frontend-build）
- **测试**：后端 40+ 单测 + 10+ smoke，前端 Vitest 组件 & store 测试

**技术栈**：Vue 3 / Pinia / Vite / Vitest / marked / highlight.js / Axios / FastAPI / SQLAlchemy / LangChain / Vercel

---

## 版本 E：工程化 / DevOps 侧重版

### MyPrivateAgent — 通用智能体框架工程化实践（个人项目）

- **CI 流水线**：GitHub Actions 四 Job（backend-lint / backend-tests / quality-gate / frontend-build），其中 `backend-tests` 显式列出 28 个核心测试模块跑 unittest、额外跑 pytest + coverage（阈值 30%），`quality-gate` 生成 JSON + markdown summary 并 upload artifact
- **质量门禁**：`quality_gate_report.py` 聚合最近 14 天的 open actions / long-blocked actions，阈值可配置（`max-open-actions=10`、`max-long-blocked-actions=0`），summary append 到 `$GITHUB_STEP_SUMMARY`
- **Smoke 脚本体系**：10+ 个面向主链路的端到端冒烟脚本，覆盖认证会话、SSE 流式、错误事件、停止生成、多智能体策略、provider 故障转移、能力缺口治理等，每个脚本可独立执行也可入 CI
- **数据库迁移**：Alembic 版本化管理，启动时 `stamp head` 确保后续迁移从当前状态继续，已沉淀 3 个迁移版本（scheduler runtime tables / permission runtime scope / runtime activity tables）
- **多模式存储**：SQLite（默认 demo）/ MySQL（生产）/ 内存（Vercel 环境）三模式通过 `DB_MODE` 环境变量切换，`bootstrap.py` 启动时根据模式做差异化初始化
- **双路径部署**：Vercel 一体化（前端 dist + `/api/*` serverless）、Docker（`python:3.11-slim` + uvicorn）双路径，`vercel.json` 配置静态资源长 cache + SPA fallback
- **Doctor 自检**：`scripts/doctor.py` 启动前检查 `.env` / 数据库 / 关键目录 / 前端构建产物 / provider 配置，前端 `DoctorPanel` 可视化呈现
- **架构文档先行**：`docs/` 下 20+ 份设计稿，按"总方案 → 目标架构 → 路线图 → 子域方案 → 验收清单"组织，每次架构收敛都留存设计记录

**技术栈**：GitHub Actions / ruff / pytest / pytest-cov / Alembic / Docker / Vercel / unittest / Vitest

---

## 版本 F：一行简述（用于名片 / LinkedIn 标语）

> 从零自研通用智能体运行时框架基座（FastAPI + Vue 3 + LangChain，42K 行），参考 Claude Code 架构落地运行时一等对象、状态机、父子执行、三层能力面与治理闭环。

---

## 附：简历技巧提示

### 不要这样写（反面教材）

- ❌ "基于 LangChain 开发了一个 AI 聊天机器人" → 低估项目 90% 价值，且面试官会默认你是包了一层 API
- ❌ "实现了一个类似 ChatGPT 的系统" → 和项目实际定位完全不符，基座不是产品
- ❌ "使用最新的 AI 技术" → 没有信息量，面试官会直接跳过
- ❌ 堆砌技术关键词不解释 → "使用 LangGraph / Pydantic / SSE / SQLAlchemy" 不如说清楚解决了什么问题

### 这样写更有说服力

- ✅ 先说定位（"框架基座，不是业务应用"），再说规模，最后说技术点
- ✅ 技术点带**数字**和**位置**（1,800 行 AgentHarness、20+ 张表、40+ 单测、10+ smoke）
- ✅ 讲**解决了什么真实问题**（流式工具调用按 index 分块聚合、provider 自动降级），而不是堆名词
- ✅ 主动提**待完善项**（类型化记忆、三级策略、coverage 30%），反而显得成熟
- ✅ 强调**方法论**（协议先行、文档先行、小步迭代），这是高级工程师的硬通货

### 面试时的临场技巧

1. **先铺架构再讲细节**：拿出 `project_overview.md` 第 3 节的六层分层图，3 分钟讲完骨架
2. **把 `docs/` 打开给面试官看**：20+ 份设计稿本身就是实力证据
3. **现场跑 smoke 脚本**：`python scripts/chat_stream_smoke.py` 30 秒证明主链路能走通
4. **被问"还有什么不足"时**：直接翻到 `project_overview.md` 第 11 节，8 条债务一条条讲清楚
