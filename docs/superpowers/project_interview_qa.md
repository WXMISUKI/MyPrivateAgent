# MyPrivateAgent 面试深度问答

> 这份文档准备给技术面试官可能追问的问题提供"可讲到底"的应答稿。每条答案都指向代码中真实存在的位置，便于面试时现场翻开对照。

---

## A. 架构类追问

### A1. 为什么要自己写 AgentHarness，不直接用 LangGraph？

> 我确实用了 LangChain 的 `bind_tools` 和 message 类型做接口兼容，也装了 `langgraph==0.2.56`。但核心执行循环自研，原因有三：
>
> 1. **LangGraph 的 graph 抽象偏"开发者手动连线"**，不适合做"运行时能力合同 + 状态机 + 事件协议"这种需要强 invariant 的底座。我需要的是一个 while-loop 级别的最小核心，再在外面包治理、记忆、Skill、MCP，而不是把所有东西塞进一个 graph。
> 2. **流式工具调用分块聚合** 在 LangGraph 里没有开箱即用的方案。豆包流式返回 `tool_calls` 时按 `index` 分块，每次可能只给一小段 JSON 片段，还会出现同一片段重复推送。我写了 `StreamingToolCallTracker`（`backend/harness/agent_harness.py:51`）按 index 聚合、去重、容错解析，还配了 `json_repair` 兜底。
> 3. **错误分类与 provider 降级** 在通用循环里没有统一抽象。我在 `ErrorHandler` 里把异常归一到 5 类，可重试的走指数退避，失败后上浮到 `ProviderFailoverAnalyticsService` 统计降级率。这个链路我不希望被框架内部逻辑覆盖。

### A2. 状态机为什么用白名单迁移表？

> `backend/agent_framework/runtime.py` 里 `_STATE_TRANSITIONS` 是 `dict[AgentState, set[AgentState]]` 的显式白名单。`transition_to()` 里一发现非法迁移就 **直接抛 ValueError**。这样做的原因：
>
> - 状态机是整个项目的"骨架"，任何一次"悄悄绕过"都会污染 run trace
> - 白名单显式列出，新增状态时所有可能的迁出/迁入都要显式决策，避免漏
> - 运行时抛错比日志告警有效得多——让问题在开发阶段就暴露，而不是在生产数据里沉淀

当前 11 个状态、50+ 条迁移边，每条边背后都有 planner、scheduler、permission、approval 的业务语义。

### A3. `AgentRun / ChildRun / AgentEvent` 为什么一定要做成一等对象？

> 因为不做成一等对象，整个项目会滑向"metadata 拼接"的深渊。典型反模式是：planner item 的 JSON 字段里塞一个 `subagent_metadata`，里面再塞一个 `execution_state`。这种嵌套 metadata 有三个必死症状：
>
> 1. **查询不了**：无法按 child 状态做 SQL 聚合
> 2. **回放不了**：状态迁移散在 JSON 里，没有统一事件流
> 3. **扩展不了**：新增一类子执行（background / worktree）就又得新开一个 metadata 字段
>
> 我在 `backend/models.py` 里显式建表：`SchedulerRunRecord / ChildRunRecord / BackgroundRunRecord / WorktreeRunRecord / PermissionRequestRecord / ArtifactRecord / CapabilityRemediationRecord`。Alembic 里有 `002_scheduler_runtime_tables / 003_permission_runtime_scope / 004_runtime_activity_tables` 三个迁移版本，记录了从 metadata 升级到一等对象的过程。

### A4. 事件协议为什么设计成 `payload` + 顶层字段双入口？

> 看 `backend/agent_framework/events.py:40` 的 `to_dict()`：事件既有标准顶层字段 (`type / event_id / run_id / parent_run_id / conversation_id / iteration / payload`)，又把 `payload` 的键展平到顶层。这是**前后兼容的过渡设计**：
>
> - 新消费者按顶层标准字段读，稳定可靠
> - 旧消费者（之前按扁平 payload 读的前端组件）仍然可以工作
> - 演进过程中允许逐步迁移消费者，不需要一次性 big-bang 重构
>
> 这种设计哲学体现在 `extract_event_field()` 辅助函数（`backend/services/chat_service.py:57`）里，读取时两边都兼容。

---

## B. 并发与可靠性

### B1. SSE 断线、用户中断生成怎么处理？

> 几层兜底：
>
> 1. **客户端主动中断**：前端 `ChatView` 把 AbortController 传到 fetch，中断后后端检测到流关闭会写入 `stop_reason='client_abort'` 的事件
> 2. **迭代预算**：`AgentHarness.max_iterations=10`，超出后强制进入 FINALIZING
> 3. **相似调用防抖**：`max_similar_tool_calls=2`，避免模型陷入死循环
> 4. **错误事件兜底**：`scripts/chat_error_event_smoke.py` 验证流式 error 事件能被前端展示
> 5. **空响应兜底**：`scripts/chat_empty_response_smoke.py` 验证上游返回空时后端仍会发出可展示的兜底回复 + `done`

### B2. 工具调用失败时的降级策略？

> 分三层：
>
> - **工具级**：`ErrorHandler.classify_error()` 把异常归类，可重试的走指数退避（1s → 2s → 4s...最大 60s），最多 `max_retries=3`
> - **Provider 级**：`ProviderFailoverAnalyticsService` 统计当前 provider 失败率，超阈值触发切换到下一家（顺序默认 `volcengine-ark → anthropic → openai`）
> - **能力级**：如果某类能力反复失败，`CapabilityGapService` 会把它标为缺口，系统后续给出"建议补工具 / Skill / MCP"的方向
>
> 这三层的好处是失败信号不会丢——会同时落 run trace、provider analytics、capability gap 三个视图。

### B3. 权限审批会阻塞执行吗？

> 会，但是有兜底。`AgentState.WAITING_PERMISSION` 是状态机里的显式状态，进入这个状态后：
>
> - 当前 run 暂停迭代，`PermissionRequestRecord` 持久化
> - 前端 `GovernanceTimelinePanel` 展示待审批项，管理员审批后后端通过 SSE 推送 `tool_permission_granted / tool_denied` 事件
> - 有超时兜底（默认几十秒），超时后自动拒绝并写入 audit
>
> 当前版本审批偏"单层"，企业级三级策略覆盖（组织 / 项目 / 用户）和正式 `ApprovalEngine` 对象在 `docs/general_agent_framework_target_architecture.md` 5.3 节有规划。

---

## C. 数据与持久化

### C1. 为什么默认用 SQLite？

> **Demo 部署优先**。`config.py` 的 `DB_MODE` 默认是 `sqlite`，数据落 `.myagent/app.db`。理由：
>
> - 面试官 / HR 本地跑 demo 不需要装 MySQL
> - Vercel serverless 函数可以挂载本地文件（或用 Turso / Neon 替换）
> - 实际要切 MySQL 只需改环境变量，没有代码改动（`DB_MODE=mysql`）
>
> 详见 `docs/demo_storage_architecture_plan.md`。

### C2. 反馈幂等怎么做的？

> 三层：
>
> 1. 数据库层：`MessageFeedbackRecord` 表有 `uq_message_feedback_conv_msg_user` 唯一约束（`(conversation_id, message_id, user_id)`），在 `bootstrap.py:_ensure_feedback_uniqueness_constraint()` 里启动时确保存在
> 2. 服务层：同一用户同一消息的反馈采用 upsert 语义，不是 insert
> 3. 数据治理：`scripts/dedupe_message_feedback.py` 提供 dry-run + apply 两段式的重复数据清理工具
>
> 这是典型的"幂等要从数据库约束开始保证"的实践。

### C3. 迁移管理怎么做？

> Alembic。当前 3 个迁移版本：
>
> - `002_scheduler_runtime_tables` — child run 一等化
> - `003_permission_runtime_scope` — 权限请求运行时作用域
> - `004_runtime_activity_tables` — 运行时活动表
>
> `bootstrap.py:_stamp_alembic_head_if_needed()` 启动时 stamp head，让后续迁移能从当前状态继续。

---

## D. 治理与可观测性

### D1. RunTrace 和 Audit 有区别吗？

> 有。`docs/general_agent_framework_target_architecture.md` 4.4.3 节显式说了：
>
> - **RunTrace**：面向运行态和回放，事件密度高，保留时间相对短
> - **Audit**：面向治理与合规，粒度粗，保留时间长
>
> 两者共用事件源但查询视角不同。当前实现仍偏一张"统一 trace 表"，正式拆分是下一阶段工作。

### D2. Quality Gate 怎么跑？

> `scripts/quality_gate_report.py` 聚合最近 14 天的治理数据，产出两份：
>
> - `quality-gate-report.json`：完整 JSON
> - `quality-gate-summary.md`：markdown summary，CI 里 append 到 `$GITHUB_STEP_SUMMARY`
>
> 阈值控制：`--max-open-actions 10`、`--max-long-blocked-actions 0`。CI 把报告 upload 为 artifact（见 `.github/workflows/ci.yml` 的 `quality-gate` job）。

### D3. Doctor 检查哪些东西？

> `scripts/doctor.py` 启动前自检：
>
> - `.env` 是否存在且合法
> - 数据库连接是否可达（SQLite 目录存在 / MySQL 可连）
> - 关键目录是否就位（`.myagent` / `backend/data`）
> - 前端构建产物 `frontend-vue/dist` 是否存在
> - 默认模型 provider 配置是否合法（至少 ARK 或 Ollama 其一）
>
> 运行时对应的服务是 `DoctorRuntimeService`，前端有 `DoctorPanel` 可视化。

---

## E. Skill / MCP / Memory 能力面

### E1. Skill 的 frontmatter 契约是什么？

> 每个 Skill 文件头是 YAML frontmatter：
>
> ```yaml
> ---
> name: xxx
> description: xxx
> tags: [xxx]
> triggers: [xxx]
> agent_roles: [frontend, backend]
> required_capabilities: [search, weather]
> priority: 10
> activation_mode: auto
> ---
> ```
>
> `SkillRuntimeService` 运行时按 tokens 匹配 triggers、按 agent_role 过滤、按 priority 排序、按 `required_capabilities` 做硬门控。匹配结果以 system prompt 注入的形式进循环。
>
> 当前 `activation_mode` 主要是 `auto`，`context_mode=inline/fork/background` 在目标架构里规划，还未落地。

### E2. MCP 当前支持到什么程度？

> 四件套：
>
> - `McpRegistryService` — 持久化 server 配置（stdio / http transport）
> - `McpSessionService` — session 管理（当前偏短连接）
> - `McpRuntimeService` — `tools/list` / `tools/call` 协议调用
> - `McpAdapterService` — 把 MCP tools 适配到 harness 的工具注册表
>
> 前端 `McpManagementPanel` 支持配置、健康探测、能力目录浏览。长连接 session 复用和正式 audit trail 还在完善（`docs/mcp_registry_framework_plan.md`）。

### E3. 记忆分层具体怎么加载的？

> `MemoryManager` 按顺序加载：
>
> 1. `GLOBAL_AGENT.md`（项目根） — 通用主协调智能体身份宣告
> 2. `PROJECT_AGENT.md`（项目根） — 项目规则层
> 3. `PROJECT_AGENT.local.md`（项目根 gitignore） — 本地覆写
> 4. `AgentMemoryService` 的运行时条目（数据库）
>
> 拼装时前面是 system prompt 的 Identity 段，后面是 Capability Profile 和 Skill 注入。这部分还是偏"静态加载"，类型化记忆（user / feedback / project / reference）和相关性召回是下阶段工作。

---

## F. 前端

### F1. 为什么前端用 Vue 不用 React？

> 两个原因：
>
> 1. 个人习惯 + 项目启动时选型偏保守（Vue 3 Composition API 对单人项目心智负担更小）
> 2. 治理面板密集的管理台场景，Pinia + `<script setup>` 的开发效率我认为更高
>
> 权衡：牺牲了更大的 React 生态（shadcn/ui、Radix 等），但换来了更短的迭代周期。如果下个项目是纯 toB 管理台，可能还会选 Vue；如果是需要大量复杂 UI 组件库的场景，会重新评估。

### F2. SSE 流式怎么渲染工具调用卡片？

> `ChatView` 收到每个 AgentEvent 后按 type 分发：
>
> - `content` → 追加到 `ChatMessageItem` 的 markdown 渲染
> - `tool_call_start` / `tool_result` → 创建 / 更新 `AgentStructuredCard`
> - 如果 tool 声明了 `card_schema`（如 weather → `WeatherCard`），按 schema 渲染
> - 未声明的落到通用 `AgentStructuredCard`
>
> 协议在 `docs/agent_framework_card_schemas.md`，前端 schema registry 在 `frontend-vue/src/components/cards/registry.js`。

### F3. 前端有测试吗？

> 有。`frontend-vue/src/components/__tests__/` 和 `stores/__tests__/` 下有 Vitest 测试，覆盖核心组件和 store 的主要路径。另外 `skill_store/dev-browser` 是一个独立的 TS skill 包，有自己的 Vitest 测试。
>
> 承认不足：Vue 主 app 的测试覆盖还不够深，没做 E2E（playwright 或 cypress），TS 化也没做。

---

## G. CI / 部署

### G1. 你的 CI 做了什么？

> 四个 job（`.github/workflows/ci.yml`）：
>
> 1. `backend-lint` — `ruff check backend/`
> 2. `backend-tests` — 显式列出核心 unittest 模块，已包含 `runtime_contract_smoke / runtime_contract_snapshot / runtime_surface / framework_adapter` 相关回归，额外跑 pytest + coverage（阈值 30%，当前 continue-on-error，逐步往严收紧）
> 3. `quality-gate` — 跑 `quality_gate_report.py`，其中已串联 `runtime_contract_smoke.py`、`RuntimeSurfacePanel` 前端 smoke，并把 summary append 到 `$GITHUB_STEP_SUMMARY`，upload 两份 artifact
> 4. `frontend-build` — `npm ci && npm run build` 验证生产包
>
> 承认不足：还没做 coverage 强门禁、没做前端 lint 门禁、没做 API 契约兼容性校验（OpenAPI diff），也还没把 runtime contract smoke 单独拆成 required status check。

### G2. Vercel 一体化部署怎么配的？

> `vercel.json`：
>
> - `buildCommand`: `cd frontend-vue && npm install && npm run build`
> - `outputDirectory`: `frontend-vue/dist`
> - Routes 把 `/api/*` 路由到 `api/index.py`（Python serverless 入口），`/assets/*` 走长 cache，其它都 fallback 到 `/index.html`（SPA）
>
> 后端在 Vercel 环境下 `VERCEL=1` 时走内存存储（检测见 `McpRegistryService:__init__`）。生产建议挂 Turso 或外部 MySQL。

---

## H. 工程决策类追问

### H1. 你觉得这个项目最大的设计缺陷是什么？

> 一个：**权限模型还是单层**。当前 `PermissionService` + `PolicyEngine` 只做到"工具级 + 角色白名单"，缺真正的组织 / 项目 / 用户三级策略覆盖，也没有独立的 `ApprovalEngine` 一等对象。企业级 SaaS 场景下这个差距是硬伤。好消息是目标架构稿里已经有详细设计（`target_architecture.md` 5.3），下阶段就会补。
>
> 另一个是**类型化记忆缺位**——目前的记忆层更像"文件加载器"而不是"受治理的长期上下文系统"，召回、漂移校验、审批、版本都还没做。

### H2. 如果重来一次，哪些地方会不一样？

> 三件事：
>
> 1. **更早做 Alembic**：初期 schema 变更靠 `create_all`，后来一等对象升级的时候补迁移是个不小的工作量
> 2. **前端直接上 TypeScript**：现在前后端契约靠文档同步，每次接口变更都要人肉对齐
> 3. **更早定 Card Schema 协议**：工具结果渲染早期是各个组件自己 switch case，后来统一到 `card_schema` 时改造面很大

### H3. 这个项目的技术债你怎么管理的？

> `docs/` 下 20+ 份文档里有几个专门记录技术债和演进的：
>
> - `general_agent_framework_enterprise_plan.md` 第 4 节"当前差距分析" — 运行时、调度、记忆、能力面、治理、工程六类差距
> - `claude_alignment_improvement_plan.md` — Claude 对齐的 P0 / P1 / P2 分级
> - `framework_execution_roadmap.md` — 阶段性工作
> - `feedback_learning_governance_plan.md` — 反馈与学习治理专项
>
> 每次改动前先更新对应的 plan，再动代码。这不是形式主义——它是我保证"单人项目不会失控"的核心方法。

### H4. 你怎么测试这种强异步 + 流式的系统？

> 分层测：
>
> - **单元测**：runtime / events / 核心 service 都有纯函数级别的单测（`tests/agent_framework/test_events.py` 等）
> - **集成测**：`test_agent_harness_cache.py`、`test_agent_harness_tool_args.py` 用 mock model 测循环各种分支
> - **Smoke**：`chat_stream_smoke.py`、`chat_empty_response_smoke.py`、`chat_error_event_smoke.py`、`chat_stop_generation_smoke.py` 跑真实 HTTP → SSE 主链路
> - **Router 测**：`test_router_imports.py`、`test_health_router.py` 等测 FastAPI 装配
>
> 承认不足：没有针对并发场景（多 child run 同时跑）的压测，没有 provider 真实流式故障注入。

---

## I. 你自己对这个项目的评价

### I1. 如果 1 分表示业务项目一个简单功能，10 分表示能独当一面的企业级开源框架，你给这个项目打几分？

> 6 分左右。
>
> - 到 6 的原因：运行时一等对象、状态机、事件协议、父子执行、治理闭环、能力面、可观测性都已落地，主链路稳定，有文档，有测试，有 CI，有部署。
> - 不到 8 的原因：类型化记忆、三级策略、ApprovalEngine 一等化、长连接 MCP session、worktree 隔离、API 契约闭环都还没做。
> - 不到 10 的原因：离真正"多人协作可持续演进"还差多租户、RBAC、正式审计导出、以及跑在生产流量下的成熟度。
>
> 这个 6 分不是谦虚，是我对"成熟开源框架应该是什么样"有真实认知的体现。

### I2. 你最自豪的一段代码或一次设计？

> 把 `run trace` 从"planner item 的附属能力"升级为"run 原生能力"这次重构。过程大致是：
>
> 1. 先写架构稿（`target_architecture.md` 5.2 节），把边界讲清楚
> 2. 新建 `RunTraceService` 作为统一入口，旧消费者通过适配层先迁移
> 3. `AgentEvent` 协议加 `run_id / parent_run_id` 字段，保留 payload 扁平化向后兼容
> 4. 逐个把 scheduler / subagent / policy / hook / mcp 的 trace 调用点切过去
> 5. 最后一轮清理，确认没有绕过 `RunTraceService` 的直写
>
> 整个过程既没有大爆炸重构，也没有留旁路。这是"协议先行 + 小步迭代"的真实案例。
