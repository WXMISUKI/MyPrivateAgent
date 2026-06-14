# 下一阶段硬化路线

> 本文记录 Phase E 之后的优先级。它不是长期愿望清单，只列当前最值得做的工程动作。

## 1. 当前结论

当前底座已经完成第一轮收口，不建议再大范围重写。基于 `D:\AI\AIcode\claude-code`、`D:\AI\AIcode\learn-claude-code`、`D:\AI\AIcode\self-improving-agent` 的本地参考阅读，下一阶段需要从治理台展示回到 Agent Runtime 主干。

项目正式定位已经收口为企业级 `Agent Runtime Control Plane`：

- 不再把 MyPrivateAgent 定义为某个外部 Agent 框架的替代实现。
- LangGraph、OpenAI Agents SDK、Qwen-Agent、CrewAI、DeerFlow、Agno 等成熟框架后续只能作为 execution adapter、lifecycle mapping、tool/handoff/tracing 参考进入项目。
- 本项目继续保有 Runtime Core、ToolRuntime、Query Control、Runtime Contract Gate、Governance Timeline、审计、权限和业务系统集成的稳定控制面职责。
- 垂域智能体资产已开始通过 `backend/domain_agents/*/agent.yaml` 和 Runtime Surface `domain_agent_registry` 进入只读登记面，执行路由仍沿用现有 chat/runtime seam。
- 任何外部框架接入默认先走 OpenSpec adapter proposal 与 promotion gate，不直接进入主 chat 执行链。

下一阶段应优先做三件事：

1. Self-Improvement Ledger 从能力契约推进到健康摘要。
2. Query Control Plane 设计与最小后端 contract。
3. Embedded SDK / Execution Loop 继续向真实 LLM、ToolRuntimeService、reviewer、fallback 接线。

同时可以在不改变主执行链的前提下，继续补齐垂域 agent catalog 的治理能力：下一步宜围绕 agent enable/disable、`GET /api/agents` 只读包装接口、manifest 驱动的 Tool/Skill/MCP 关联校验逐个开小 change，而不是一次性做完整 agent marketplace。

Governance Timeline 前端继续瘦身仍有价值，但不应继续作为最高优先级。

### Provider Capability Roadmap 补充

Provider-first 能力路线已补充到 `docs/roadmap/provider_capability_gap_assessment_2026-06-03.md`，并通过 OpenSpec `provider-capability-roadmap` 固化为后续方向。当前优先级顺序是：

1. 继续 `plan-external-rag-graphrag-provider`，等待外部 RAG / GraphRAG provider readiness 后做 caller-side readiness 与 smoke；不要把 LlamaIndex、Neo4j、向量库或图数据库引入主后端。
2. 新开 `add-agent-grounding-policy-contract`，先定义 `require_citations / allow_ungrounded / fallback_policy / source_acl_mode`，再谈默认 chat 检索注入。
3. 新开 `add-promptops-versioned-prompt-contract`，把 `/prompts` 从 CRUD 升级为版本、变量、评测、审批、灰度、回滚合同。
4. 新开 `add-agent-memoryops-lifecycle-contract`，区分 hot session、conversation summary、长期记忆与 retrieved evidence。
5. 新开 `add-multiturn-agent-evaluation-gate`，用多轮场景回归验证 prompt/RAG/context 行为。
6. P2 的多模态 taxonomy、workflow/chatflow、企业 connector 和 provider ops 后置到 P0/P1 control contract 稳定之后。

外部 RAG / GraphRAG provider 仍在开发时，MyPrivateAgent 内部控制面按 `docs/roadmap/internal_agent_control_tasks_2026-06-03.md` 推进；当前 active internal slice 是 `add-agent-grounding-policy-contract`，只做 grounding policy 可见性和合同收口，不改变默认 `/api/chat` 检索行为。

### Provider Post-Closure Rule

`unifiedKnowledgeRAG` provider 收口后，下一阶段默认不是继续扩 provider 内部能力，而是优先完成真实 caller 闭环验证。当前推荐执行入口已经固定为：

- `docs/integration/phase26-caller-provider-live-trial-closure/phase26-caller-provider-live-trial-runbook.md`
- `docs/integration/phase26-caller-provider-live-trial-closure/phase26-caller-provider-live-trial-task-pack.md`

此阶段把 `D:\AI\AIcode\经验总结与复用目录\知识库与RAG\RAG_Techniques` 视为 strategy candidates，而不是默认 backlog。以下方向在没有真实 trigger 前不进入当前主线：

- query rewrite
- rerank
- hybrid retrieval
- GraphRAG execution

只有满足以下 trigger 之一，才允许 reopen provider enhancement：

- `real_caller_feedback_trigger`
- `provider_owned_gap_trigger`
- `repeated_cross_source_failure_class_trigger`
- `runtime_strategy_evaluation_trigger`

当前 MyPrivateAgent 侧补充收口：

- Knowledge Provider capability health / heartbeat 已新增只读 `governance_readiness`，可区分显式 RAG ready、source catalog degraded、GraphRAG gated 与 default chat grounding gated。
- Domain-agent grounded-answer promotion gate 已优先消费 `provider_evidence.governance_readiness`：显式 RAG ready 可进入文档 RAG trial 判断，source catalog degraded 进入 review，provider unreachable blocked，GraphRAG gated 继续阻止 graph trial。
- Domain-agent grounded-answer trial surface 已把 provider readiness 提升为顶层 compact `provider_readiness` 摘要，显式保留 ready/review/blocked 与 GraphRAG gated 解释，供后续 package dry-run / composition trial 使用。
- Grounded-answer package dry-run 已继续保留 trial report 的 compact `provider_readiness`，形成未来答案组合前的受治理输入包；该输入包仍不调用 provider/model/chat，不执行 GraphRAG，也不创建 source binding。
- 该 readiness 不改变默认 `/api/chat` 行为，不创建 source binding，不执行 GraphRAG，也不修改答案策略。
- 后续若继续推进，应优先进入 grounding policy / eval-backed promotion，而不是继续扩 provider-side RAG 策略。

## 1.1 Phase G：外部参考对齐后的新增方向

已完成第一刀：

- 新增 `backend/services/self_improvement_ledger_service.py`
- Runtime Surface 暴露 `self_improvement_ledger`
- Runtime Contract Snapshot 守护 `self_improvement_ledger` 稳定字段
- 新增 Phase G 文档：`docs/change/2026-05-16-phase-g-agent-runtime-reference-alignment.md`
- Self-Improvement Ledger 已新增 `health_summary`，并通过 `/api/runtime-profile` 在真实 Health Router 中读取当前数据库统计
- Runtime Contract Snapshot 已守护 `self_improvement_ledger.health_summary`
- Self-Improvement Governance Timeline Adapter 已完成第一刀，`learning` 事件写入 trace / audit 的逻辑已从 router helper 下沉到 `SelfImprovementTimelineService`
- Error / Feature Request 创建与更新已接入 Self-Improvement Timeline Adapter，支持 `source = error` / `source = feature_request` 的治理事件回放
- Self-Improvement Timeline 事件已统一生成并返回稳定 `dedupe_key`，支持后续前端聚焦与治理重复分析
- Self-Improvement Timeline 已接入 `dedupe_key` 写入幂等；当 persisted trace 已存在同 key 时跳过重复 trace / audit 写入
- Query Control Plane 已完成 contract 第一刀，Runtime Surface 暴露 `query_control_plane`，Runtime Contract Snapshot 已守护其生命周期字段
- Query Control Timeline Adapter 已完成第一刀，支持按统一 lifecycle stage / execution channel 写入 `source = query_control` 的 trace / audit，并复用 persisted trace `dedupe_key` 幂等
- Embedded SDK 已完成 Query Control lifecycle mapping 第一刀，可把现有 SDK / ExecutionLoopController 事件映射为 `input_received / planning / model_stream / tool_decision / tool_execution / observation / review / final_output`
- External Adapter Pilot 已完成 Query Control lifecycle mapping 第一刀，可在显式注入 recorder 时把 `framework_adapter_status / reasoning / output / external_error` 映射到 `external_adapter` 通道
- Subagent Lane 已完成 Query Control lifecycle mapping 第一刀，可把 `child_run_created / subagent_spawned / subagent_collected / subagent_merged` 映射到 `subagent_lane` 通道
- Scheduler fan-out 已显式调用 Subagent Query Control helper，记录 spawn / collect / merge 三段生命周期，不改变前端 `scheduler_merged` 输出 contract
- Main chat 已完成核心执行生命周期 mapper / helper 落地，并通过 execution context 开关接入 `opt-in + fail-open` 的 Query Control timeline recorder 第一刀
- 普通 chat 已支持通过 request-level `execution_context` 显式开启 `main_chat` timeline recorder，默认行为仍保持关闭
- `ChatRequest.execution_context` 已收敛为白名单专家入口 contract，避免普通 chat API 暴露成任意 runtime metadata 注入口
- 聊天页前端已新增 `Runtime Trace / 专家模式` 开关，可在不污染默认用户路径的前提下透传受控 `execution_context`
- Runtime Surface 已新增统一 `Main Chat Trace` 设置卡片，聊天页与治理面板现共享同一前端状态源
- Runtime profile 已新增 `main_chat_trace_overview`，前端可直接查看最近一次 `main_chat` Query Control trace 是否真的写入
- `governance_overview` 已新增 `main_chat` 概览，`main_chat` trace 状态已进入统一治理总览语义
- Governance Timeline 已支持按 `main_chat` domain 过滤 `query_control` trace，`main_chat` 生命周期已具备“概览 + 列表回放”双入口
- `main_chat_trace_overview` 已新增阶段分布、最后成功阶段、最近告警阶段，治理面板不再只停留在 latest trace 展示
- `main_chat_trace_overview` 已新增最近 N 次 `query_id` 摘要列表，治理视角不再只停留在当前 item 的单点聚合
- Runtime Surface -> Governance Timeline 已支持 `query_id` 级 drill-down，`main_chat` 已具备从摘要列表进入单 query 时间线的最小闭环
- Governance Timeline 已新增 `Query Detail` 面板，单 query 视角已具备结构化详情而不只剩过滤后的事件列表
- `runtime-profile` 已新增正式 `main_chat_query_detail` contract，query 级详情开始从前端临时推导收口为后端正式数据面
- `runtime-profile` 已支持显式 run scope 输入，并把 `governance_overview.run` 收口为 parent overview 后端真源，前端不再需要从 child merged semantics 反推 child merge 概览字段

下一刀建议：

- G-4D：再评估主 chat 接入统一控制面事件，避免直接大改 chat 主流程。
- G-4H-6：再评估审批 / 治理事件是否需要作为补充信号进入 `main_chat` 观察面，而不是直接混入核心执行线。
- G-4H-8：评估是否需要把 `main_chat_trace_overview` 继续接入 governance overview / runtime core 概览，而不是只停留在独立卡片。
- G-4H-9：评估是否需要让治理时间线支持按 `main_chat` channel 直接过滤，而不是只能在 Runtime Surface 里查看最近摘要。
- G-4H-10：评估是否需要把 `main_chat` 的 stage 分布、最后成功阶段、最近失败阶段进一步结构化到治理总览卡，而不是只展示 latest trace。
- G-4H-15：评估是否需要把 `main_chat_query_detail` 继续扩展成 query 级详情接口或分页历史接口，而不是只挂在 runtime-profile 上。

## 1.2 Phase H：Runtime Core 与 Query/Run Read Model 收口

### 阶段目标

- 把当前已经跑通的 `main_chat` 治理观察链路，从“局部可见”收口到 Runtime Core 与 Query/Run Read Model 主干。
- 把后续优先级从局部展示增强切回运行时对象模型、治理读模型和后端 contract 一致性。
- 让维护者只看本文件，就能知道下一阶段做什么、做到哪、何时应停止继续优化。

### 为什么现在做

- `main_chat` 观察面当前已达到“可观测、可筛选、可 drill-down、可 query 级查看”的阶段完成线。
- 后续如果继续把主要精力投入在 `main_chat` 局部 UI 微优化，收益会快速下降，并且容易重新迷失在小方向里。
- 当前最值得收口的是：
  - Runtime Core 术语与对象模型
  - Query/Run 治理读模型
  - 跨 Runtime Surface / Governance Timeline 的统一 contract
- 因此，下一阶段最高优先级切回 Runtime Core 与 Read Model，而不是继续追加局部展示增强。

当前收口决策：

- `child_run_id` 是 Runtime Core 正式术语，`child_execution_id` 只保留为兼容键。
- `query` 表示用户请求完整生命周期，`run` 表示其中一次执行实例。
- `trace` 与 `audit` 保持并列但不复制，`artifact` 与 `snapshot_ref` 继续维持上位对象与引用形态的关系。
- `main_chat` query history 已完成专用 read model 和浏览壳收口，非 `main_chat` channel 扩展不进入本阶段主线。

### 本阶段任务清单

#### H-1：Runtime Core 名词与对象模型收口

目标：

- 统一 `query / run / child_run / scheduler_run / approval / artifact / trace / audit / memory / skill / adapter` 的语义边界。
- 明确 durable state 与 runtime state 的分层。
- 明确 control plane 与 execution plane 的责任边界。

完成定义：

- 相关术语在架构文档、runtime contract、治理视图文案中一一对应。
- 不再出现前端、后端、文档对同一概念各自命名的情况。
- 运行时相关 contract 能明确回答“这是什么”和“它不是什么”。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `main_chat / subagent / external_adapter / embedded_sdk` 已进入同一 Query Control 生命周期语言
  - `main_chat` 已具备 query 级治理观察闭环
- 进行中：
  - 运行时对象模型仍分散在多个 service / view / contract 中表达
  - `docs/architecture/runtime_contracts.md` 已开始补 Runtime Core 术语收口第一刀
  - `docs/architecture/runtime_contracts.md` 已新增“术语 -> contract 字段 -> 前端展示 -> 当前判断”的第二刀对照表
  - `child_run_id` 已开始进入前端展示与 scheduler 对外 contract 断言主字段位
- 未开始：
  - 术语与对象模型的统一收口文档

下一步动作：

- 优先收口 `query / run / child_run / approval / trace` 五个核心对象。
- 以 `docs/architecture/runtime_contracts.md` 为真源，补充“是什么 / 不是什么”的定义段。
- 基于术语对照表，筛出真正需要动代码统一命名的漂移点，优先评估 `query_id vs run_id`、`child_run_id vs child_execution_id`、`artifact vs snapshot_ref`。
- 当前优先级判断：
  - 第一优先级：`child_run_id vs child_execution_id`
  - 第二优先级：`query_id vs run_id`
  - 第三优先级：`artifact vs snapshot_ref`
- 当前已补出 `child_run_id` 最小收口方案：
  - `child_run_id` 作为 Runtime Core 正式术语
  - `child_execution_id` 作为 scheduler/runtime repository 兼容键
  - 先统一文档与 contract，再决定是否做数据库/实现层迁移
 - 当前已执行的最小代码收口：
   - `PlannerPanel` 已优先展示 `child_run_id`
   - `SchedulerService` 相关测试已把 `child_run_id` 固定为对外 contract 主字段断言之一
   - `SchedulerService.build_execution_context()` 已新增 `child_label`，并固定其优先取值为 `child_run_id`
   - `SchedulerService._serialize_child_execution()` 已新增 `child_display_id`，作为对外稳定展示字段，优先等于 `child_run_id`
   - `SchedulerService.get_scheduler_snapshot()` 与 `PlannerService.serialize_plan()` 已打通 `child_display_id`，前端 `scheduler_snapshot.children` 与 `child_executions` 都开始共享同一主展示标识

是否继续优化：

- 是

停止条件：

- Runtime Core 关键术语在文档、contract、前端展示中不再漂移。
- 新增治理需求不再需要先解释“这个字段到底代表什么”。
- 第一批高漂移双名对象已排定清晰的收口顺序，不再并行发散处理。
 - `child_run_id` 的正式术语定位已固定，不再回到“两个名字都可以”的状态。

#### H-2：Query/Run Read Model 后端化

目标：

- 继续把当前前端推导的 `main_chat` / `query` 视图后端化。
- 收口 `main_chat_trace_overview / main_chat_query_detail / governance_overview` 的边界。
- 明确哪些是 summary contract，哪些是 query-level detail contract。

完成定义：

- 前端主要消费后端 read model，而不是继续堆叠前端推导逻辑。
- query 级详情已有正式 contract，而不是只靠通用 timeline 推断。
- `runtime-profile` 或后续 query 级接口能够稳定输出 query 详情所需字段。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `main_chat_trace_overview`
  - `governance_overview.main_chat`
  - `main_chat_query_detail`
  - `recent_queries`
- 进行中：
  - query 级详情已开始由后端正式 contract 驱动，但前端仍保留部分推导 fallback
  - `GovernanceTimelinePanel` 的 `Query 摘要` 已优先消费后端 `main_chat_query_detail`，不再默认完全依赖前端从通用 timeline 推导
  - `main_chat_query_detail` 已新增 `latest_summary / stage_count / warning_count / recent_events`，query 级视图开始更明显地转向 read model 驱动
  - 已新增独立接口 `/api/runtime-profile/main-chat-query-detail`，`GovernanceTimelinePanel` 开始直接消费 dedicated query detail contract，而不是继续通过 `runtime-profile` 曲线取值
  - 已新增 dedicated history endpoint `/api/runtime-profile/main-chat-query-history`，开始把 `recent_queries` 之外的 query 历史摘要从 canonical spec 推进到实现层
  - `RuntimeSurfacePanel` 已新增最小 query history 消费壳，支持分页摘要展示与“加载更多”验证链路
  - `GovernanceTimelinePanel` 已新增最小 query history 浏览壳，支持在 `main_chat` 域下查看历史摘要并继续 drill-down 到单 query
  - Governance 侧 `main_chat history` 搜索态已进入视图复制/恢复链路，可分享带筛选的历史浏览上下文
  - Governance 侧 `main_chat history` 页码已进入视图复制/恢复链路，可恢复“已加载到第几页”的历史浏览状态
  - `MainChatQueryHistoryPanel` 已补齐历史指标、当前聚焦提示与就地清理动作，开始具备更独立的治理历史面板体验
  - `GovernanceTimelinePanel` 已把 query history 与 query detail 收进同一 `Main Chat Query Workspace`，开始形成更完整的治理历史工作区
  - `main_chat_query_detail` 已新增 `associated_run_ids` 关联执行实例集合，明确 `query_id` 仍是 query detail 主身份，`run_id` 只作为关联执行实例语义进入 read model
- 未开始：
  - 更完整的 query history 独立治理交互壳

下一步动作：

- 继续把 dedicated query detail / history endpoint 扩成更稳定的 query 级 read model 入口，并评估是否需要进一步强化 cursor 模式。
- 继续减少 `GovernanceTimelinePanel` 对通用 timeline 推导 query 详情的依赖，把可稳定字段逐步后端化。
- 让 `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 尽量共享同一份 query detail contract 解释逻辑。
- 评估 `main_chat_query_history` 是否需要从当前最小浏览壳继续升级为独立治理历史面板。
- 评估是否要把 history 的更多浏览上下文纳入 route-driven 恢复，而不只恢复 query/stage/search/page。
- 评估是否要为独立历史面板补更明确的分页状态区、双栏布局或更强的 query/detail 联动。
- 评估是否要继续把 workspace 做成更明显的双栏治理台交互，而不只是当前最小分区收口。
- 当前结论：`main_chat` query history 已经完成独立 read model、前端浏览壳和 workspace 收口，后续不再优先扩展到非 `main_chat` channel。若未来要扩展，应先复用当前 `query_history / query_detail / recent_queries` 三层边界，再单独立项评估。
- 当前优先级：把 query/read model 的边界写死，并维护共享解释 helper；不要继续给 history 追加新 channel，也不要把 `associated_run_ids` 误读成 run 级 detail promotion。

是否继续优化：

- 是

停止条件：

- query 级详情的核心字段已有后端正式 contract。
- 前端不再需要为了 query 详情继续新增复杂推导逻辑。
- `main_chat` 历史体验已达到当前阶段完成线，后续优化应转向 Runtime Core 与 Read Model，而不是继续在 `GovernanceTimelinePanel` 上做局部扩展。

#### H-3：治理视图统一化

目标：

- 让 Runtime Surface、Governance Timeline、未来治理台共用同一组 domain / filter / query 语义。
- 减少“这个页面能看、那个页面不能看”的断层。

完成定义：

- `main_chat / framework_adapter / mcp / permission / scheduler` 的治理入口一致。
- route filter、overview card、detail contract 的语义不再冲突。
- 从 summary 到 timeline drill-down 的跳转路径稳定且可复用。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `main_chat` 已进入 Runtime Surface、Governance Overview、Governance Timeline 三层视图
  - 支持 `main_chat` domain filter 与 `query_id` drill-down
- 进行中：
  - 单 query 详情仍主要挂在通用治理时间线之上
  - `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 已开始共享 `frontend-vue/src/services/governanceViewInterpretation.js` 中的 query/history contract 解释逻辑
- 未开始：
  - 更统一的 query 级详情交互壳

下一步动作：

- 评估是否需要为 `query_id` 级详情提供独立视图或更强的聚合面板。
- 继续减少不同面板间同义字段展示不一致的问题。

是否继续优化：

- 是

停止条件：

- 用户从 Runtime Surface 到 Governance Timeline 的跳转不再需要二次理解语义。
- 主要治理入口对同一事件的命名、过滤、定位方式保持一致。

#### H-4：外部参考项目映射沉淀

目标：

- 把 `learn-claude-code / self-improving-agent / claude-code` 的借鉴点沉淀成可复用映射表。
- 明确“借什么、不借什么、落到我方哪个模块”。

完成定义：

- 外部参考不再只是讨论时的灵感来源，而是进入正式设计输入。
- 后续讨论不会再反复回到“这个项目能不能借鉴”。
- 每个参考项目都能映射到我方的 runtime core / governance / adapter / hook 等模块。

当前状态：

- 进行中

当前进度：

- 已完成：
  - 已基于本地参考阅读修正 Phase G 后续方向判断
  - 已新增第一版正式参考映射文档：`docs/architecture/reference_project_mapping.md`
  - 已新增第一版 Spec Kit 项目宪章：`.specify/memory/constitution.md`
  - 已补 `openspec/config.yaml` 项目上下文与 proposal/tasks/archive 默认规则
  - 已创建第一份真实 OpenSpec change：`openspec/changes/decouple-main-chat-query-read-model/`
  - 已创建第二份真实 OpenSpec change：`openspec/changes/add-main-chat-query-history-pagination/`
  - 已创建第三份真实 OpenSpec change：`openspec/changes/generalize-query-workspace-boundary/`
  - 已创建第四份真实 OpenSpec change：`openspec/changes/pilot-subagent-lane-recent-summary/`
  - 已新增第一份 OpenSpec canonical spec：`openspec/specs/query-run-read-model/spec.md`
  - 已新增第二份 OpenSpec canonical spec：`openspec/specs/query-workspace-generalization/spec.md`
  - 已新增 `openspec/README.md`，把本仓库的 OpenSpec 工作流说明落地
- 进行中：
  - 把外部参考从“方向判断”继续沉淀成可复用设计输入
  - 把 spec-driven 治理规则与现有 architecture / roadmap 真源建立稳定互链
- 未开始：
  - 把参考映射继续扩展到更细的模块级落点与后续 action item

下一步动作：

- 继续补强 `docs/architecture/reference_project_mapping.md`，并在关键架构文档处建立互链。
- 如后续新增参考项目，沿用同一模板：参考点 / 借鉴价值 / 不借鉴边界 / 我方落点模块。

是否继续优化：

- 是

停止条件：

- 外部参考已转化为稳定设计输入，不再依赖对话记忆反复解释。

### 当前进度面板

- 阶段判断：
  - `main_chat` 相关链路已达到阶段完成线，不再是最高优先级优化对象。
  - 当前最高优先级已切回 Runtime Core 与 Query/Run Read Model 收口。
  - `child_run_id vs child_execution_id` 已完成低风险对外收口第一阶段，可暂不继续深入到数据库/兼容层改造。
  - 当前应把 H-1 的主要注意力切到第二优先级 `query_id vs run_id`，避免继续在已接近完成线的小收口上消耗。
- 当前最值得推进：
  - H-1 Runtime Core 名词与对象模型收口
  - H-2 Query/Run Read Model 后端化
  - H-4 外部参考项目映射沉淀
  - `generalize-query-workspace-boundary`：收口哪些 query 能力已经可以从 `main_chat` 提升为通用模式
  - `pilot-subagent-lane-recent-summary`：以最小试点方式验证第一个非 `main_chat` channel 的 query summary 推广
  - `channel-promotion-gate`：把 channel 推广顺序和 readiness checklist 提升为独立真源
- 当前可以暂缓：
  - 单纯追加 `main_chat` 展示字段
  - 继续堆叠更多筛选器而不增加 runtime 收口价值
  - 继续把 `child_execution_id` 这条线推进到数据库迁移或 repository 内部重构
  - 继续扩大 `child_display_id` 的内部传播范围，直到真正出现对外 contract 不一致的证据
- 当前已完成 `query_id vs run_id` 的最小收口方案判断：
  - `query_id` 作为 Query Control / 治理观察主键
  - `run_id` 作为 Runtime Core 执行实例主键
  - 当前优先继续统一 contract 与前端文案，不急着改底层 fallback 逻辑
- 当前已执行的最小展示收口：
  - `RuntimeSurfacePanel` 已把 `run` 视角与 `query` 视角文案拆开显示
  - `GovernanceTimelinePanel` 已把 `当前 Run` 收口为 `当前执行实例`
- 当前阶段判断：
  - `query_id vs run_id` 已完成最小文案收口第一阶段
  - 后续若继续推进，优先进入 read model / contract 收口，不再把主要精力放在继续细抠外层标签
  - `H-2` 已进入“dedicated endpoint + shared contract helper”阶段，当前最值得继续的是把 query 级 read model 进一步从 `runtime-profile` 中解耦出来
  - `H-2` 当前已从单 query detail 扩展到 query history read model，下一步最该补的是前端消费壳，而不是重新回到只补字段
  - `H-2` 当前已把 `main_chat_query_detail` 补入自描述元数据（`read_model_layer / source_channel / identity_kind`），后续治理面板应优先消费这些显式字段
  - Runtime Surface / Governance Timeline / Query Detail / Query History 已轻量展示 query read model metadata，治理阅读时可以直接确认 layer/source/identity，不再只依赖隐藏 contract 字段
  - `main_chat_query_history` 已完成后端 contract + Runtime Surface / Governance Timeline 最小消费壳，下一步重点应转向更完整的独立治理历史体验
  - `RuntimeSurfaceService.get_runtime_profile()` 已拆出独立 profile assembler，后续 profile 扩展应优先沿这个边界推进，而不是继续把组装逻辑堆回主方法
  - `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 已统一到 `frontend-vue/src/services/governanceViewInterpretation.js` 这层 shared interpretation facade
  - 当前治理历史浏览已具备“可浏览、可筛选、可复制、可恢复页码与搜索、可就地清理聚焦”雏形，后续优化应优先增强独立交互壳，而不是重复堆字段
  - 当前 `main_chat` 治理历史已经形成 workspace 雏形，后续若继续做，应优先增强布局与联动体验，而不是继续零散补状态参数
  - `governance_overview.run` 已成为 parent overview 的后端真源，后续 parent merge 显示不应继续从 child merged semantics 反向拼装
  - 下一步更值得做的不是继续深挖 `main_chat` 局部体验，而是收口“通用 Query Workspace / Query History 边界”，判断哪些能力已可从 `main_chat` 提升为通用模式
  - `query-workspace-generalization` 已正式升格为 canonical spec，后续高层通用化判断应优先以它为真源
  - `channel-promotion-gate` 应作为后续一切多 channel readiness / promotion 讨论的第一参考，而不是继续复制某次 change 里的 checklist
  - 在这份高层边界 change 写清之前，不建议把 `main_chat` 专项体验直接外推到 `subagent_lane` 或 `external_adapter`
  - 下一步若继续推进多 channel，优先做 `subagent_lane / external_adapter` 的 readiness checklist 判断，而不是直接讨论它们的 history/workspace 壳
  - `subagent_lane` 当前已通过 `recent summary` readiness 评估，可作为第一个非 `main_chat` 的轻量推广候选；但在 dedicated detail contract 稳定前，不进入 `query detail / query history / query workspace`
  - `pilot-subagent-lane-recent-summary` 第一刀已完成：后端 dedicated contract、Runtime Surface 最小入口和 focused tests 已落地
  - `external_adapter` 当前也已通过 `recent summary` readiness 评估；但在 dedicated detail contract 稳定前，同样不进入 `query detail / query history / query workspace`
  - `subagent_lane recent summary` 试点既然已落地，下一步需要在“继续做 `external_adapter recent summary` 对称试点”和“先暂停多 channel 扩展、回到更高层 query workspace 边界收口”之间做明确选择
  - 当前默认推荐先暂停继续扩 channel，优先回到高层边界判断；只有在确实需要对称验证时，再单独开启 `external_adapter recent summary` 试点
  - 因此，`external_adapter recent summary` 当前不是默认下一步；除非出现明确对称验证需求，否则不建议现在继续开新试点实现
  - `subagent_lane query detail readiness` 已作为后端门禁 contract 开始收口：先判断 stable query id、stage chain candidate、recent summary recorded、child-run identity separation，再决定是否另开 dedicated detail contract
  - `subagent_lane query detail` 已落地为 dedicated backend contract；它只覆盖单 query lifecycle detail，不扩大到 history/workspace，也不替代 child executor 输出回放合同
  - `decouple-main-chat-query-read-model` 的剩余 follow-up 已评估完成：`recent_queries` 仍保持轻摘要，query detail 继续走 dedicated endpoint，runtime-profile 只保留兼容面
  - `H-4` 第一版正式映射文档已落地，后续可直接基于文档继续吸收外部经验，而不是依赖对话记忆

### 阶段收束建议

- `H-1` 当前已完成第一阶段命名收口，除非出现新的对象语义冲突，否则不再作为本阶段最高优先级实现方向。
- `H-2` 已把 `main_chat` 从 query detail 推进到 query history 与 workspace 雏形，并开始把 query detail 契约显式自描述化；当前更适合从“继续做局部实现”切回“收口 read model 通用边界”。
- `H-3` 已形成 Runtime Surface / Governance Timeline 的最小统一体验；下一步应以治理工作区的整体布局和模式判断为主，而不是继续堆零散交互。
- `H-4` 已完成第一轮参考映射和 spec-driven 规则落地，足以支撑下一阶段做更抽象的底座判断。
- 因此，当前推荐工作模式从“连续功能实现”切换为“阶段收束 + 下一阶段规划”。

### 当前收束结论

当前建议将 `Phase H` 视为**接近阶段完成线**，原因如下：

1. `main_chat` 这条主线已经具备：
   - dedicated query detail
   - dedicated query history
   - Runtime Surface 入口
   - Governance Timeline 工作区
   - 搜索 / 分页 / 恢复 / 复制 等治理浏览基础能力
2. `subagent_lane` 与 `external_adapter` 的推广边界已经明确：
   - 两者都只通过了 `recent summary` readiness
   - 两者都还不能进入 detail/history/workspace
3. `query workspace` 已有独立 canonical spec，可承接下一阶段更高层的统一化判断。

因此，当前不建议继续默认扩展新的 channel 实现；更合理的做法是：

- 先对 `Phase H` 做阶段收束
- 再决定下一阶段是否进入：
  - 通用 query workspace/read model 进一步抽象
  - 或新的多 channel 轻量试点

### 建议的下一阶段输入

如果下一轮要进入新的阶段，建议至少带着以下输入启动：

- `query-workspace-generalization` canonical spec
- `query-run-read-model` canonical spec
- `reference_project_mapping`
- 当前 `Phase H` 的收束结论

这样下一阶段就不会再从局部功能出发，而会从底座模式和边界判断出发。

## 1.3 Phase I：Query Workspace 通用化与 Channel Promotion Gate

### 阶段目标

- 把 `main_chat` 已经跑通的 query 模式，从“单一 channel 的成熟实现”收口成更稳定的通用基准。
- 明确哪些 query 能力可以在不同 channel 间逐层推广，哪些能力必须继续保持 channel-specific。
- 让后续任何多 channel 扩展都先经过 readiness / gate 判断，而不是继续复制 `main_chat` 的局部产品壳。

### 为什么现在做

- `Phase H` 已经把 `main_chat` 做到 query detail、query history、workspace 雏形，并把 query detail 契约开始做自描述收口，继续深挖局部体验的收益开始下降。
- `subagent_lane` 与 `external_adapter` 都已经完成 `recent summary` readiness 判断，但还没有进入更深层；这正适合进入“推广规则和 gate 机制”阶段，而不是继续凭感觉扩功能。
- `query-workspace-generalization` 已升格为 canonical spec，说明当前最需要的不是再做一条新实现线，而是让高层边界成为后续实现的前置约束。

### 本阶段任务清单

#### I-1：Query Workspace Canonicalization

目标：

- 把 `query-workspace-generalization` 从规格真源推进成架构真源中的稳定高层概念。
- 明确 `recent summary / query detail / query history / query workspace` 四层在 architecture、roadmap、OpenSpec 中的统一表达。

完成定义：

- 团队讨论 query 模式时，默认先引用 canonical spec，而不是从某个 UI 或某条历史实现推断。
- 架构文档、roadmap、OpenSpec README 对 query workspace 的定义和分层保持一致。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `openspec/specs/query-workspace-generalization/spec.md` 已建立
  - `docs/architecture/runtime_contracts.md` 已新增 Query Workspace 通用化边界段落
  - `docs/architecture/current_architecture.md`、`docs/README.md`、constitution 已建立入口
- 进行中：
  - 已把“何时结束单 channel 深挖、何时转向高层判断”的模式同步进 roadmap、architecture、OpenSpec README 与 constitution
- 未开始：
  - 更明确的 Phase I canonicalization 验收说明

下一步动作：

- 继续压实 architecture / roadmap / OpenSpec 三条线的术语一致性。
- 明确 query workspace 真源与 runtime contract 真源的边界，避免两者互相吞并。
- 默认不继续恢复新的 channel 实现，除非高层真源之间再次出现冲突或后续出现明确的对称验证需求。

是否继续优化：

- 是

停止条件：

- 高层 query workspace 概念不再依赖口头解释。
- 任何新扩展讨论都能先落到 canonical spec 再展开。

#### I-2：Channel Promotion Gate

目标：

- 把 channel 推广顺序从“经验判断”收口成正式 gate。
- 让 `main_chat -> recent summary -> query detail -> query history -> query workspace` 的逐层推广路径具备清晰门槛。

完成定义：

- `subagent_lane` 和 `external_adapter` 的当前层级判断被正式固化。
- 后续若新增 channel，团队知道它应该先争取进入哪一层，而不是直接索取完整 workspace。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `subagent_lane` 已通过 `recent summary` readiness 判断
  - `external_adapter` 已通过 `recent summary` readiness 判断
  - `pilot-subagent-lane-recent-summary` 第一刀已完成
  - promotion record 已固化为恢复 channel 实现前的前置 gate，记录字段包括 channel、current layer、target layer、readiness evidence、blockers、decision、next allowed action 和 non-goals
- 进行中：
  - 当前 decision 已记录为：`external_adapter` 仍是 `recent_summary` candidate，但默认 `spec_only`，不立即做对称实现
- 未开始：
  - 将 promotion record 扩展成运行时可观测 payload 的必要性评估

下一步动作：

- 未来新增 channel 或恢复 channel 实现时，先补 promotion record，再决定是否进入代码实现。
- `subagent_lane` 不得直接推进到 history/workspace；若要推进，必须另开 promotion decision。
- `external_adapter recent summary` 仍不是默认下一刀，除非出现明确对称验证需求并记录 resume decision。

是否继续优化：

- 是

停止条件：

- 团队对“先做哪一层，再做哪一层”的判断不再摇摆。
- 不会再因为局部 momentum 就越级推进 history/workspace。

#### I-3：Generic Recent Summary Abstraction

目标：

- 在不越级做 detail/history/workspace 的前提下，评估是否需要把 `recent summary` 这一层进一步抽成更通用的 assembler / contract 模式。

完成定义：

- 明确哪些字段是所有 channel 都能共享的最小集合。
- 明确 `main_chat recent_queries`、`subagent_lane recent summary`、未来 `external_adapter recent summary` 之间哪些字段可以同构。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `main_chat` 与 `subagent_lane` 的最小 recent summary 形态都已有事实样本
  - shared recent summary 字段集合已固定为 `query_id / latest_stage / latest_summary / latest_timestamp / recording_state`
  - `external_adapter_recent_summary` 已作为第二个轻量样本落地，但仍只停留在 recent summary 层
- 进行中：
  - 已给出当前推荐结论：先不抽通用 assembler / service，先写死共享字段集合
- 未开始：
  - 在第三个非 `main_chat` channel 真实进入 recent summary 后复评是否抽象

下一步动作：

- 继续保持 channel-specific builder，但把共享字段集合固定成稳定口径。
- 只有在第三个 channel 真正落地、或当前多个 builder 已经出现明显重复且维护成本上升后，再复评是否值得抽象成通用 assembler。
- 当前 promotion record 不要求 generic assembler；它只要求实现 slice 不再临时发明 recent summary 主字段。

是否继续优化：

- 是

停止条件：

- 团队已接受“当前先不抽”的结论，并知道何时再复评。
- 无论结果如何，都不再在每个 channel 上临时发明字段。

#### I-4：Phase I Exit Gate

目标：

- 给 `Phase I` 本身补一个清晰退出条件，避免它像 `Phase H` 一样边做边延长。

完成定义：

- 能明确回答“什么时候可以从通用化判断切回新一轮实现”。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `Phase H` 已给出收束建议和下一阶段输入
- 进行中：
  - 已补出恢复实现与继续停留在规格层的第一版判断条件
- 未开始：
  - 把 exit gate 与后续真正恢复实现的触发规则收成团队默认口径

下一步动作：

- 明确：
  - 何时允许重新开启多 channel 实现
  - 何时应该继续停留在规格和架构层
- 当前 exit gate 口径：只有当高层真源稳定、channel promotion gate 已记录正式决策、recent summary 抽象判断明确、下一步实现从该 channel 当前允许的最浅层开始，并且本次 change 明确列出不会越级推进的非目标时，才允许恢复新的 channel 级实现。
- 若 promotion record 缺失、目标层级摇摆，或下一步会同时触碰 detail/history/workspace 多层能力，则继续停留在规格/架构层。
- 当前默认下一刀不再是新的 channel 功能实现，而是先执行 promotion record discipline；完成后再重新判断是否恢复 `external_adapter recent summary` 或继续停留在边界收口。

是否继续优化：

- 是

停止条件：

- `Phase I` 自身具备明确 exit gate，不会再无限延长。

### Phase I 启动条件

- `Phase H` 已接近收束完成。
- `query-run-read-model` 与 `query-workspace-generalization` 两份 canonical spec 已稳定存在。
- `main_chat` 已是完整 baseline。
- 至少一个非 `main_chat` channel 已完成 `recent summary` 试点或 readiness 判断。

### Phase I 执行入口

当前进入 Phase I 时，默认先执行一次 channel promotion review，而不是直接进入代码实现。推荐使用项目 skill：

- `.codex/skills/myagent-channel-promotion-review/SKILL.md`

该 review 必须回答：

- 当前评估的 channel 是什么。
- 当前允许停在哪一层：`readiness / recent_summary / query_detail / query_history / query_workspace`。
- 下一步是否需要新 OpenSpec change。
- 哪些层级必须阻断，以及阻断原因。
- 如果允许实现，最小可验证切片是什么。

当前默认结论：

- `main_chat` 是 canonical baseline，不再默认继续深挖局部体验。
- `subagent_lane` 已具备 recent summary 和 dedicated query detail，但不得直接推进到 history/workspace。
- `external_adapter` 已具备 recent summary 轻量试点，但不得直接推进到 detail/history/workspace。

### Phase I 暂缓事项

- 默认不继续深挖 `main_chat` 局部体验。
- 默认不立即开启 `external_adapter query_detail` 或更深层对称试点。
- 默认不推进任何 channel 的 `query history / query workspace` 新实现。

### Phase I 收束标准

- 团队对 query 能力的四层模型、推广顺序和 gate 已形成统一判断。
- 至少能明确最近 summary 是否值得做通用抽象。
- 可以清楚回答：下一步该恢复实现，还是继续停留在高层边界收口。
- 当前结论：Phase I 可以按 promotion boundary 收束，不要求 `subagent_lane / external_adapter` 达到 workspace parity。

### Phase I 恢复实现条件

只有在以下条件同时满足时，才建议从 `Phase I` 切回新的 channel 级实现：

- `query-run-read-model` 与 `query-workspace-generalization` 两份 canonical spec 已稳定
- `channel-promotion-gate` 已可作为统一模板复用
- `recent summary` 是否抽象已有明确当前结论
- 团队对下一个试点 channel 的层级目标无分歧
- 若目标是推进 `subagent_lane history/workspace` 或 `external_adapter detail/history/workspace`，必须另开 promotion decision change，并且目标层只能从当前已批准层向下一层推进。

### Phase I 继续停留在规格层的条件

如果出现以下任一情况，则默认继续停留在规格/架构层，不恢复新的 channel 实现：

- 新增 channel 的推广顺序还在摇摆
- canonical spec 之间仍存在边界冲突
- 团队对 channel-specific / generic 的边界还没统一
- 当前只是因为“局部 momentum”想继续扩实现，而不是因为高层判断已完成

## 1.4 Phase II：Runtime Core 恢复实现与交付面瘦身

当前默认入口：

- Phase I 已按 query workspace promotion boundary 收束。
- 下一刀默认从 Phase II 中选择，不再默认扩展 channel query 能力。
- 若后续重新打开 channel promotion，必须先回到 `channel-promotion-gate` 写明 reopen decision。

### 阶段目标

- 在 `Phase I` 已把高层 query/read model 与 channel promotion gate 收口清楚之后，恢复**底座级高价值实现**。
- 优先推进那些能显著提升底座成熟度、却不会把团队重新拉回局部 UI 小优化的主线。
- 让 `Runtime Core / Capability / Governance / Delivery` 四层的下一轮实现重新回到有顺序、有 gate 的推进节奏。

### 为什么现在做

- `Phase H` 已把 `main_chat` 做到 query detail、query history、workspace 雏形，并开始显式收口 query detail 元数据，继续深挖局部体验的收益开始下降。
- `Phase I` 已明确：
  - query 能力四层模型
  - channel promotion gate
  - recent summary 抽象当前先不做
  - 何时恢复实现、何时继续停在规格层
- 因此，下一阶段最合理的动作不再是继续补高层 spec，而是**恢复底座主线实现**，但只恢复高价值方向。

### 本阶段任务清单

#### II-1：Embedded SDK 持久化与恢复能力

目标：

- 把 `EmbeddedAgentRuntimeSDK` 从当前 memory-first preview 进一步推进到更接近业务可嵌入的版本。
- 优先解决持久化、恢复、continuation、child executor 这些真正影响底座成熟度的问题。

完成定义：

- SDK 不再只适合短时内存态演示，而具备更稳的恢复/重进能力。
- 后续垂域项目可更放心地以库的方式接入 Runtime Core。

当前状态：

- 进行中

当前进度：

- 已完成：
  - `create_run / stream_events / submit_approval / resume_run / delegate_run / execute_run` 第一刀
  - approval continuation / loop continuation 最小闭环
  - runtime contract smoke 与 quality gate 基线
- 进行中：
  - 已把 SDK 当前易失状态边界、continuation 恢复边界和后续 persistence seam 写入 architecture / roadmap / SDK 注释，避免后续实现阶段继续边做边定义
  - 已新增 `backend/agent_framework/continuations.py`，把 `tool_approval_continuation / loop_continuation` descriptor 结构与状态更新路径收口成统一 helper
  - 已明确 `resume_run(..., continue_loop=True)` 当前只应被视为 in-process recovery seam；在 continuation persistence seam 稳定前，不把它视为跨进程恢复入口
  - 已明确 `delegate_run(...)` 当前只应被视为 child run relationship seam；在 child run 恢复边界、上下文预算和 merge 语义收清前，不把它视为真实 child executor 起点
  - 已新增可注入 `EmbeddedRunWorkspaceStore` seam，并通过默认内存实现打通 run snapshot / events / approvals / continuation descriptor 的统一读写边界
  - SDK 已支持从 workspace store 回填 run snapshot / events / approvals，并在仅有 persisted continuation descriptor 时显式 fail-closed
  - 已新增 `probe_run_recovery(run_id)` 正式 recovery probe seam，并把 `recoverable / unrecoverable`、`recovery_reason`、descriptor/executable availability 写回 metadata 与 persisted continuation descriptor
  - `submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 已接入同一套 fail-closed recovery gate；当只有 persisted descriptor、缺少 executable continuation 时，会标准化写入 `recovery_failed_closed`
  - 已新增 `EmbeddedContinuationRegistry` seam；当 continuation descriptor 具备稳定 binding id，且当前 SDK 能从 registry 解析 binding 时，tool continuation / loop continuation 已可在新进程里完成受控 reattach
  - recovery reason 已扩展为可区分 `ready_in_process / ready_via_registry / missing_registered_binding / missing_executable_continuation`，说明 II-1 已从“只会判断”进入“有条件重挂执行能力”的阶段
  - 已把 continuation binding 从“字符串约定”推进到标准 catalog 面；registry 现在能输出 `binding_id / binding_kind / handler_name / metadata`，SDK 也能通过 `list_continuation_bindings()` 暴露只读 binding 清单
  - `build_embedded_sdk_contract()` 与 `build_agent_harness_facade_contract()` 已正式暴露 `delegate_preflight`；`delegate_run(...)` 返回值与 child run metadata 也会同步携带 `relationship_only` 级别的 child executor 前置判断
  - Runtime Surface 已新增 `embedded_runtime_boundaries` 读模型与治理卡片，维护者可直接查看 `delegate current scope / promotion requirements / non-goals / approved reference slices`
  - `delegate_preflight` 已从静态说明推进到最小可执行判断：当 payload/metadata 显式提供 child context budget、merge semantics 与 worker runtime backend 时，可升级为 `promotion_candidate`，否则继续保持 `relationship_only`
  - `child_executor_preflight` 已从边界附属信息升级为独立 read model，同时挂在 `runtime_profile` 与 `governance_overview.child_executor_preflight`，前端与治理台应直接消费该 contract
  - `child_executor_promotion_gate` 已成为独立 backend truth source，同时挂在 `runtime_profile` 与 `governance_overview.child_executor_promotion_gate`；它当前统一返回 `gate_status / allowed / failure_reason / blockers / executor_path / recommended_next_step`
  - recovery probe 与实际 reattach 路径已开始感知 `workspace_backend` 状态；内存态或 fallback 激活的 workspace backend 不再误判为 `ready_via_registry` 的跨进程恢复来源
  - `run_recovery` 已成为 dedicated runtime surface read model，并通过 `/api/runtime-profile/run-recovery` 暴露；当前可统一表达默认 `descriptor_missing` 场景，以及 `durable workspace + registry` 下的 `ready_via_registry` 场景
  - 默认 embedded runtime 依赖已开始通过 `EmbeddedRuntimeDependencies / EmbeddedRuntimeFactory` 统一注入；SDK、Facade 与 Runtime Surface 的默认构造不再各自拼 `workspace_store / continuation_registry`
  - `embedded_runtime_factory` 已进入 `runtime_profile` 主画像；默认 runtime 的 `db_mode / embedded_workspace_store_mode / default_runtime_mode / recovery_posture` 现在已有统一后端真源
  - SDK persistence interface 已完成第一刀：`persistence_interface.persistence_posture` 统一表达 `memory_preview / durable_ready / durable_degraded`，并从 workspace backend description 派生，不再依赖临时 durable flag 或前端推断
  - SDK / Facade / Runtime Surface 已开始共享同一 persistence posture 真源；默认 runtime contract、recovery probe、`embedded_runtime_boundaries` 与 `default_runtime_recovery` 都会透出 compact `persistence_interface`
  - SDK 已新增 durable recovery operation contract；实际 `submit_approval.approved` 与 `resume_run.continue_loop` 恢复尝试会记录 `recovered / blocked` operation evidence，便于生产排障从“是否可恢复”下钻到“某次恢复尝试发生了什么”
  - Runtime Surface `run_recovery` 已新增 recovery operation read model，正式透出 `recovery_operation_boundary / latest_recovery_operation / recovery_operation_history / recovery_operation_count`，后续治理消费方无需再扫描 SDK metadata 或 event sample
  - Recovery operation contract construction 已从 `sdk.py` 抽到 `backend/agent_framework/recovery_operations.py`，SDK 主类只保留恢复操作记录时机与持久化编排，后续恢复协议继续硬化时 locality 更清晰
  - Worker ownership 已完成最小 in-memory seam：`claim_run / heartbeat / validate_ownership / get_lease` 固定 lease/fencing 语义，recovery operation record 也可接收 compact ownership evidence
  - Worker ownership 已新增 SQLAlchemy durable adapter 第一刀：`runtime_worker_ownership_leases` 持久化 run-level lease/fencing，支持跨 store instance 读取、竞争 claim 阻断、过期替换递增 fencing、heartbeat 保持 token 与 stale fencing fail-closed；但默认 runtime dependency 仍是 in-memory，数据库 vendor 专用分布式锁、自动续租与 SDK 恢复入口自动 claim 仍是后续切片
  - Worker ownership 默认装配已新增 `WORKER_OWNERSHIP_STORE_MODE`：默认 `memory_only`，可显式切到 `prefer_sql_with_fallback / strict_sql`；runtime factory contract 会暴露 `worker_ownership_store_mode / worker_ownership_store_mode_source`，但 SDK recovery gate 仍只在 descriptor ownership evidence 存在时执行
- Worker ownership store mode 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 守护：`worker_ownership_store_mode` check 会覆盖默认 memory-only、strict SQL、prefer fallback 与 bootstrap knob 暴露，summary 归一化为 `runtime_contract_summary.worker_ownership_store_mode_coverage`
- Worker ownership production gate 已落地第一刀：runtime factory contract 会暴露 `worker_ownership.production_gate`，strict SQL row lease/fencing 仍因 vendor lock semantics、后台 renewal supervisor、rollout checklist、auto-claim policy 与 audit evidence 缺口保持 `overall_status = blocked`，默认生产 ownership enforcement 不会启用
- Worker ownership production gate 已补齐 audit evidence readiness：`worker_ownership.ownership_audit` 与 `ownership_audit_evidence` section 会解释 compact evidence、operation history、recovery operation link、timeline writer、idempotent dedupe 与 authorization-source posture，且 audit evidence 只能作为阻断/诊断证据，不能替代 lease validation 或默认生产授权
- Worker ownership production gate 已补齐 vendor lock semantics readiness：`worker_ownership.vendor_lock_semantics` 与 `vendor_lock_semantics` section 会解释 lock adapter、lock scope、fencing guarantee、failover semantics、TTL/renewal semantics、stale owner cleanup 与 production allowment 缺口；strict SQL row lease/fencing 仍只能作为 `sql_row_lease_fencing` posture，不会被误判为 vendor-specific distributed lock
- Worker ownership vendor lock target decision gate 已补齐：`worker_ownership.vendor_lock_semantics.policy.target_decision` 与 production gate 的 `vendor_lock_semantics` section 现在会机器可读地暴露目标 backend、adapter kind、scope、fencing、TTL/renewal、failover、stale cleanup 与 production allowment 决策缺口；当前仍不实现 vendor-specific lock adapter，SQL row lease/fencing 仍不能作为 vendor lock 授权
- Worker ownership vendor lock target decision input source 已补齐：`target_decision.input_source` 与 production gate 的 vendor lock section 现在会解释 target decision 来源于 config、ops decision record、rollout artifact 或 manual approval metadata 的哪一类证据；默认缺 decision source、approval、backend/adapter 仍 blocked，不把 SQL row lease/fencing 当作 vendor lock 来源
- Worker ownership vendor lock adapter seam 已补齐：`worker_ownership.vendor_lock_semantics.policy.adapter_contract` 与 production gate 的 vendor lock section 现在会解释 adapter kind、target backend、scope、fencing、TTL/renewal、failover、stale cleanup、acquire/renew/release/probe capability 与 production allowment 缺口；默认仍 blocked，不执行真实 vendor lock acquire/renew/release/probe，不把 SQL row lease/fencing 当作 vendor lock 授权
- Worker ownership PostgreSQL vendor lock probe contract 已补齐：Postgres advisory lock backend 现在可通过 `adapter_contract.backend_probe` 描述 advisory lock family、lock key derivation、scope、fencing binding、TTL/renewal、failover、stale cleanup 与 probe safety；默认 blocked 且 `executes_probe=false`，不连接 PostgreSQL、不执行 advisory lock SQL、不启用 production default ownership
- Worker ownership PostgreSQL advisory lock execution seam 已补齐：`PostgresAdvisoryLockExecutionSeam` 提供显式 opt-in 的 `probe_once / acquire_once / renew_once / release_once` envelope，只有调用方注入 executor 才会执行；默认无 executor 时 fail-closed，不连接 PostgreSQL、不启动后台循环、不启用 production lock allowment。该 seam 已嵌入 `adapter_contract.backend_probe.execution_seam`，并进入 production gate、runtime smoke、Quality Gate 与 Runtime Contract Gate evidence
- Worker ownership production gate 已补齐 production enablement strategy readiness 与 default enablement input source：`worker_ownership.production_enablement_strategy` 与 `fail_closed_default_decision` section 会解释 required sections、blocking sections、显式 enablement 请求、production default allowment、input source、all-required-sections readiness 与 SQL row lease 不能作为默认授权；`worker_ownership.production_default_enablement_input_source` 会解释 config / ops decision record / rollout artifact / manual approval 来源、request、approval、strict SQL target、rollout artifact、vendor lock decision、renewal lifecycle、auto-claim decision、audit、rollback 与 fallback evidence。默认仍保持 blocked，不启用生产 ownership enforcement
- Worker ownership PostgreSQL rollout artifact consumer 已补齐：`worker_ownership.postgres_rollout_artifact_consumer` 可以把 caller-owned rollout artifact / runtime config dict 标准化为机器可读 evidence，并在 artifact 完整且 PostgreSQL opt-in execution seam ready 时生成 nested ready `production_default_enablement_input_source`。该 consumer 默认 blocked、不读取外部 artifact、不执行 advisory lock、不启用 production default ownership，已进入 runtime smoke、Quality Gate 与 Runtime Contract Gate coverage
- Worker ownership production rollout 已补齐 operationalization evidence：`worker_ownership.production_rollout.operationalization` 与 `rollout_checklist` section 会解释 rollout mode、required/missing artifacts、rollback plan、fallback policy、renewal lifecycle verification 与 auto-claim decision 状态；默认仍保持 blocked，不执行 rollout、不启用 production ownership
- Worker ownership production rollout confirmation decision record 已补齐：`worker_ownership.production_rollout.operationalization.confirmation_decision` 与 `rollout_checklist` section 会解释 decision recorded、decision id、approver、approval time、target store mode、rollback/fallback acknowledgment、renewal lifecycle verification 与 auto-claim decision 缺口；默认仍保持 blocked，不把 rollout decision 当成 production default ownership 授权
- Worker ownership production rollout confirmation input source 已补齐：`confirmation_decision.input_source` 与 production gate 的 `rollout_checklist` section 现在会解释 rollout confirmation 来源于 config、ops decision record、deployment artifact、change ticket 或 manual approval metadata 的哪一类证据；默认缺 source kind、decision id、approval、target store mode 与 rollback/fallback/renewal/auto-claim references 仍 blocked，不把 SQL row lease/fencing 当作 rollout confirmation authority
- Worker ownership production enablement runtime config consumer 已补齐：`worker_ownership.production_enablement_runtime_config_consumer` 可把 caller-owned runtime config / rollout artifact / ops decision record / manual approval metadata 标准化为 nested `production_default_enablement_input_source` 与 `production_gate_composition_dry_run` evidence；默认 blocked，不读取文件、不拉取远程 config、不修改环境、不启用 production default、不执行 advisory lock、不启动后台 worker、不运行 recovery auto-claim，并已进入 runtime smoke、Quality Gate 与 Runtime Contract Gate coverage
- Worker ownership production enablement runtime config binding 已补齐：`RuntimeSurfaceService` 可把已物化的本地 runtime surface effective config 显式传入 `EmbeddedRuntimeFactory`，并由 factory-built `worker_ownership.production_enablement_runtime_config_consumer` 暴露 evidence；该 binding 仍只读、fail-closed、不读取外部 config、不启用 production default、不执行 advisory lock、不启动后台 worker、不运行 recovery auto-claim，并已进入 runtime smoke、Quality Gate、Runtime Contract Gate 与 Snapshot guard。
- Child executor sandbox backend adapter binding gate 已补齐：`child_executor_sandbox_backend_binding` 会要求显式 executor opt-in、ready sandbox backend adapter contract 与 callable dispatcher backend adapter 同时存在，dispatch contract 才能把 sandbox backend binding 视为 ready；默认仍不启动 worker、不写队列、不执行 retry、不合并 child result。
- Worker ownership auto-claim entrypoint allowlist 已补齐只读 contract：默认 allowlist 明确 `submit_approval.approved / resume_run.continue_loop`，并进入 auto-claim policy、production gate、runtime smoke、Quality Gate 与 Runtime Contract Gate；allowlist ready 不等于 auto-claim enabled，默认仍保持 descriptor-evidence-only 与 production gate blocked
- Worker ownership explicit auto-claim enablement gate 已补齐只读 contract：`worker_ownership.explicit_auto_claim_enablement_gate` 会解释 explicit config、production gate、durable ownership、idempotency/audit、lease validation、rollout auto-claim decision 与 allowlisted entrypoint 是否齐备；默认 `will_auto_claim=false`，并把 blocked reason 进入 production gate / runtime smoke / Quality Gate / Runtime Contract Gate
- SDK worker ownership auto-claim 已接入 explicit enablement gate 的 opt-in enforcement seam：调用方同时打开 `worker_ownership_auto_claim_enabled` 与 `worker_ownership_auto_claim_gate_enforced` 时，SDK 会先校验 production gate、durable ownership、idempotency/audit、rollout decision 与 entrypoint allowlist；阻断时不调用 `claim_run`，并把 nested gate evidence 写入 `recovery_failed_closed` 的 compact worker ownership payload。旧 opt-in auto-claim 仍兼容，默认 descriptor-evidence-only 与 production gate blocked 不变
- Worker ownership renewal supervisor 已从只读 readiness 推进到显式 opt-in execution seam：`WorkerOwnershipRenewalSupervisor.renew_once(...)` 可在调用方显式传入 owner/lease/fencing evidence 时执行一次 validate + heartbeat，并对 stale fencing / missing store fail-closed；同时已提供受控 `start(...) / stop(...) / status()` lifecycle，只有调用方显式 start 才会启动可停止续租循环，构造默认 inactive，仍不默认启用 production ownership
  - Recovery retry 已完成最小 evidence contract：`recovery_operation_contract.retry_policy` 会声明 max attempts、backoff strategy、retryable/terminal reasons；operation record 可携带 compact `retry` evidence，但自动 retry execution / scheduler 仍未实现
  - Recovery retry evidence 已新增 dedicated classifier / consumer 第一刀：`build_recovery_retry_evidence(...)` 可区分 `retryable / terminal / exhausted`，并保留 operation idempotency evidence；自动 retry execution / scheduler 仍未实现
  - Recovery audit summary 已进入 Runtime Surface `run_recovery` 读模型，可从 operation history 归纳 latest status、失败分布、retry 分布、latest retry status、latest retry terminal reason、ownership evidence 与 terminal reason；该 summary 只作为治理证据，不参与执行授权或自动 retry
  - SDK recovery gate 已支持显式 retry attempt evidence：`submit_approval(..., retry_attempt=...)` 与 `resume_run(..., continue_loop=True, retry_attempt=...)` 在 blocked / fail-closed 恢复路径会把 retry classifier 结果写入 recovery operation history；未传入 retry metadata 时默认行为不变，仍不自动 retry
  - Recovery retry evidence 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 守护：`recovery_retry_evidence` check 会验证显式 retry attempt metadata 在 fail-closed recovery path 中形成 compact evidence，summary 归一化为 `runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke`；该闭环仍不代表自动 retry scheduler 已实现
  - Recovery audit trace writer 已完成 opt-in 第一刀：`RecoveryAuditTimelineService.record_operation(...)` 可把 compact recovery operation 写入 Runtime Trace，并通过 operation-level dedupe key 跳过重复写入；当前不自动接入 SDK recovery 主流程
  - Recovery audit production gate 已完成第一刀：`recovery_operation_contract` 暴露 `recovery_audit_production_readiness`，`persistence_interface.production_recovery_gate` 可将 `recovery_audit_operation_history` 标记为 ready，Runtime Contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 已守护 `runtime_contract_summary.recovery_audit_operation_history_coverage.audit_smoke`；该能力仍只是治理证据，不是执行授权或 worker lease validation
  - SDK recovery gate 已开始 opt-in 消费 worker ownership：当 SDK 显式注入 `worker_ownership_store` 且 persisted descriptor 携带 ownership evidence 时，`submit_approval.approved` / `resume_run.continue_loop` 会先校验 lease/fencing，stale fencing 等失败会 fail-closed 并记录 blocked operation
  - Worker ownership store 已提升为 `EmbeddedRuntimeDependencies` 的一等依赖，默认 runtime factory 可把 in-memory ownership adapter 传给 SDK，并在 factory contract 中暴露 `worker_ownership` 依赖状态；显式注入 SQLAlchemy ownership store 时 contract 可报告 `adapter_kind = sqlalchemy / durable = true`
  - Runtime contract smoke 已新增 `embedded_sdk_persistence_posture` check，覆盖 memory、durable-ready 与 durable-degraded/fallback 三类证据
  - Quality Gate / Runtime Contract Gate / Snapshot 已归一化并守护 `runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke`，旧报告或证据缺失会 fail-closed
  - Durable workspace production recovery gate 已落地第一刀：`persistence_interface.production_recovery_gate` 会证明 `durable_ready` 只是 backend capability，不是默认跨进程恢复授权；descriptor lifecycle governance、registry/checkpoint production policy、loader execution handoff policy 与 recovery audit operation history 已进入 evidence 与 quality gate，worker ownership gate 与 rollout 缺失时仍为 blocked
  - Child executor promotion gate 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 守护：`child_executor_promotion_gate` check 会固定默认 relationship-only blocked 决策，summary 归一化为 `runtime_contract_summary.child_executor_promotion_gate_coverage`
  - Child executor execution prerequisites 已作为 promotion gate 的嵌套 contract 落地：默认仍保持 blocked / relationship seam preserved，并通过 runtime contract smoke、Quality Gate、Runtime Contract Gate 与 Snapshot 守护 `runtime_contract_summary.child_executor_execution_prerequisites_coverage.prerequisites_smoke`
  - Child executor context budget 已从字段存在检查收紧为 `child_executor_context_budget_policy`：默认缺失 budget source / bounded limit 时 fail-closed，显式 opt-in 样本中的 `max_turns` 可被归一化为 ready evidence，但仍不代表 worker dispatch、sandbox runtime 或远端 executor 已启用。
  - Child result merge semantics 已从字段存在检查收紧为 `child_result_merge_handoff_contract`：默认缺失 merge source / strategy / intent policy 时 fail-closed，显式 opt-in 样本中的 `append_summary` 可被归一化为 ready evidence，但仍不执行 parent merge，也不代表 worker dispatch。
  - Child executor dispatch contract 已作为真实 dispatch 前的最终 side-effect-free boundary 落地：默认 `dispatch_ready = false`、`will_dispatch = false`，并在 Runtime Surface / Embedded Runtime Boundaries / Governance Overview 中暴露。
  - Child executor dispatch contract 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 守护：`child_executor_dispatch_contract` check 会固定默认 blocked / no-dispatch 证据，summary 归一化为 `runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke`
  - Child executor backend registry 已落地：`embedded_sdk_worker` 现在是 known candidate 但 `dispatch_ready = false`，preflight 可区分 known/unknown backend，execution prerequisites 用 `worker_backend_dispatch_ready` 阻断真实 executor dispatch
  - Child executor sandbox worker backend adapter contract 已落地第一刀：真实 sandbox backend 必须先提供 adapter contract、sandbox/resource/audit/idempotency guard evidence 与 compact attempt envelope，registry / dispatch contract / dispatcher 都会对缺失 evidence fail-closed；默认 backend 仍保持 relationship-only，不启动 worker
  - Child executor sandbox worker backend execution seam 已落地：`SandboxChildExecutorBackend` 只在显式 opt-in dispatcher 调用时执行 `dispatch(...)`，valid payload 返回 compact completed envelope；unsafe payload、missing idempotency / child id、executor failure 均 fail-closed，不执行 parent merge、不调度 retry、不授权 production dispatch。
  - Child executor sandbox worker backend adapter / execution seam gate 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / health trace / Snapshot 守护：`child_executor_sandbox_backend` check 会固定 ready adapter、missing guard fail-closed、unsafe payload fail-closed、compact attempt evidence、execution seam success / blocked / failed paths 与 dispatcher invocation count，summary 归一化为 `runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke` 及 execution seam stable fields；该 coverage 仍不表示默认启用 worker、queue、sandbox runtime 或远端 executor
  - Child executor dispatch result handoff contract 已落地：`ChildExecutorDispatcher.dispatch(...)` 的成功与 blocked 路径都会携带 `dispatch_result_handoff`，用于解释 compact backend result、output/audit refs、schema guard、blocked reason、parent merge=false、retry scheduled=false 与 production dispatch authorization=false。
  - Child executor dispatch result handoff 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 守护：`child_executor_dispatch_result_handoff` check 会固定 ready sandbox result、default blocked result 与 malformed result fail-closed，summary 归一化为 `runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.result_handoff_smoke`；该 coverage 仍不执行 parent merge、不调度 retry、不默认启用 worker。
  - Child executor dispatch result retry audit policy 已落地：`dispatch_result_handoff` 现在嵌套携带 `dispatch_result_retry_audit_policy`，可区分 success/no-retry、retryable failure、terminal failure 与 missing-idempotency fail-closed；retryable 只表示 audit/idempotency evidence ready，不会调度 retry。
  - Child executor dispatch result retry audit policy 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / Snapshot 守护：`child_executor_dispatch_result_retry_audit_policy` check 会固定 not_required、retryable、terminal 与 blocked 四类 posture，summary 归一化为 `runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke`；该 coverage 仍不启动 worker、不执行 parent merge、不启用 retry scheduler。
  - Child executor dispatch retry scheduler handoff gate 已落地：`dispatch_result_retry_audit_policy` 现在嵌套携带 `dispatch_retry_scheduler_handoff`，可说明 retryable evidence 是否具备 scheduler handoff 条件；默认缺 scheduler binding 时保持 blocked，缺 idempotency / audit evidence 继续 fail-closed，terminal result 不可 handoff，显式 bound 样本也固定 `will_schedule_retry = false`。
  - Child executor dispatch retry scheduler handoff 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / health trace / Snapshot 守护：`child_executor_dispatch_retry_scheduler_handoff` check 会固定 retryable-without-scheduler、missing-idempotency、missing-audit、terminal 与 explicitly-bound-no-schedule 五类路径，summary 归一化为 `runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.handoff_smoke`；该 coverage 仍不启动 worker、不执行 retry、不启用默认 scheduler。
  - Child executor dispatch retry scheduler execution authorization dry-run 已落地：`child_executor_dispatch_retry_scheduler_binding_gate` 现在嵌套携带 `retry_scheduler_execution_authorization`，可在 binding gate、显式授权来源、scheduler contract、production scheduler gate、durable schedule state、idempotency/dedupe、audit timeline、worker ownership 与 bounded attempts 全 ready 时报告 dry-run ready；默认缺 execution authorization request 时 blocked，且固定 `will_schedule_retry = false` / `retry_scheduled = false`。
  - Child executor dispatch retry scheduler execution authorization dry-run 已进入 runtime contract smoke / Quality Gate / Runtime Contract Gate / health trace / Snapshot 守护：`child_executor_dispatch_retry_scheduler_execution_authorization` check 会固定 default blocked、ready-but-no-schedule、production-gate-blocked、missing-durable-schedule、missing-audit/idempotency 与 missing-worker/bounded-attempt 路径，summary 归一化为 `runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.authorization_smoke`；该 coverage 仍不启动 worker、不写 durable schedule、不执行 retry、不启用默认 scheduler。
  - SDK / Facade 已新增独立 child executor preflight 评估入口，可返回 `executor_binding_status / executor_binding_blockers / recommended_next_step`，为后续正式执行前 gate 做准备
  - child executor output 的 replay / compact summary 已稳定带出 `entities / focus_points / action_items`，说明 child output 已进入正式语义面，而不再只是 execution payload
  - child output merge 已开始按 `intent_label` 走最小 merge behavior 分流，并把 `child_executor_merged_semantics` 写回 parent metadata，供 replay / summary / parent state 共用
  - Runtime Surface child executor 面板也已接入 `latest_merged_semantics`，当前可直接观察 `intent_label` 与 `merge_behavior`，但仍保持只读消费，不在前端重写 merge contract
  - `parent merged semantics` 已提升为 dedicated runtime surface read model，说明 parent merge 解释已不再只作为 child artifact summary 的附属字段存在
  - child intent taxonomy 已开始收成稳定枚举，并通过 `intent_catalog_version / supported_intents` 暴露在 dedicated merged semantics read model 中
  - parent merge 结果现已具备最小 section 结构：`merged_entities / merged_focus / merged_actions / latest_conclusion`
  - parent merge 结果现已进一步进入 parent state surface：dedicated merged semantics read model 会暴露 `parent_state_surface`，Runtime Surface 的 `Run Overview` 也能直接展示 child merge intent / entities / latest conclusion
  - Parent merge sections 已补充 section metadata 与 parent state section counts：list section 暴露 `section_kind / item_count`，latest conclusion 暴露 `section_kind / text_length`，`parent_state_surface` 暴露 `section_source / section_ids / section_counts`
  - Parent merge section evidence 已提升进 `runtime_core` 与 `governance_overview.run`：overview contract 现在直接暴露 `child_merge_section_source / child_merge_section_ids / child_merge_section_counts`
- 未开始：
  - 持久化 workspace / continuation descriptor / child executor 等更高成熟度能力

下一步动作：

- SDK 持久化接口第一刀已收口，下一步只在真实 durable backend / descriptor 需求明确时继续扩展，不再新增平行的构造 flag。
- Durable workspace production recovery gate 已收口，descriptor lifecycle governance、registry/checkpoint production policy、loader execution handoff policy 与 recovery audit operation history 已完成第一刀；worker ownership production gate blocker evidence 已联动进入 durable recovery gate。worker ownership renewal supervisor readiness、rollout readiness、rollout operationalization、rollout confirmation decision record、rollout confirmation input source、auto-claim policy readiness、auto-claim entrypoint allowlist、explicit auto-claim enablement gate、production enablement strategy readiness、production default enablement input source、vendor lock adapter seam、PostgreSQL advisory lock probe contract 与 PostgreSQL advisory lock opt-in execution seam 已完成 contract / quality gate 第一刀，renewal supervisor 已具备显式 one-shot renew seam 与 opt-in controlled lifecycle，SDK opt-in auto-claim 执行路径也已可受 enablement gate fail-closed 约束；但仍没有默认 production vendor lock backend 绑定、默认生产后台续租 supervisor、真实 production rollout execution、显式 production default enablement 与默认 auto-claim 授权。后续若继续推进 `resume_run(..., continue_loop=True)` 的生产跨进程恢复，应优先把 PostgreSQL seam 接入受控 rollout artifact 或补 production enablement runtime config consumer，而不是直接默认启用。
- 判断 `delegate_run` 何时进入真实 child executor。
- 在正式恢复实现前，不默认把 SDK 当前 in-process maps 误当成 durable workspace。
- 在 continuation persistence seam 稳定前，不默认把 `resume_run(..., continue_loop=True)` 视为跨进程恢复入口。
- 在 child run 恢复边界、上下文预算和 merge 语义收清前，不默认把 `delegate_run(...)` 视为真实 child executor 起点。
- 新增 child executor 升格消费方时，优先读取 `child_executor_promotion_gate`，不从 preflight / binding / merged semantics 自行重算最终 allow/deny。
- 新增真实 child executor 执行消费方时，优先读取 `child_executor_promotion_gate.child_executor_execution_prerequisites`，确认 `ready / requirements / missing_requirements`，不要在 executor 或前端侧重算 execution readiness。
- 新增 child executor context budget 消费方时，优先读取 `child_executor_context_budget_policy`，不要把任意非空 `child_context_budget` 字段当成可执行预算；无界 budget 应继续阻断真实 executor handoff。
- 新增 child result merge 消费方时，优先读取 `child_result_merge_handoff_contract`，不要把任意非空 `merge_strategy` 字段当成 parent merge 授权；未知策略应继续阻断真实 executor handoff。
- 新增 worker backend 时，先进入 `child_executor_backend_registry` 并明确 `dispatch_ready / dispatch_mode / blockers`，不要只靠 payload 中的 backend 字符串作为真实执行授权。
- 新增真实 dispatcher 时，必须先读取 `child_executor_dispatch_contract`，确认 `dispatch_ready = true` 且后续实现显式接管 `will_dispatch` 语义；不要把 promotion gate passed 直接等同于可启动 worker。
- 新增 dispatch attempt handoff 消费方时，优先读取 `child_executor_dispatch_contract.child_executor_dispatch_attempt_handoff`，确认 default blocked、opt-in sandbox envelope validation、unsafe payload guard、audit/idempotency handoff evidence 已进入 smoke / Quality Gate / Runtime Contract Gate / Snapshot；但 handoff ready 仍只是可交接证据，不是 worker 启动授权。
- 新增 dispatch result handoff 消费方时，优先读取 dispatcher attempt 的 `dispatch_result_handoff` 或 `runtime_contract_summary.child_executor_dispatch_result_handoff_coverage`，确认 ready/blocked/malformed 三类 evidence 已被门禁覆盖；不要把 result handoff ready 解释为 parent merge 完成、retry 已调度或 production worker 已启用。
- 新增 dispatch retry 消费方时，优先读取 `dispatch_result_handoff.dispatch_result_retry_audit_policy` 或 `runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage`，确认 retryable evidence 同时具备 audit 与 idempotency；不要把 `retry_policy_status = retryable` 解释为 retry 已被调度或默认后台 scheduler 已启用。
- 新增 dispatch retry scheduler 消费方时，优先读取 `dispatch_result_handoff.dispatch_result_retry_audit_policy.dispatch_retry_scheduler_handoff` 或 `runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage`，确认 scheduler binding、audit、idempotency 与 terminal classifier 均已进入 handoff gate；不要把 handoff ready 解释为 `will_schedule_retry = true` 或默认 scheduler 已启用。
- 新增 dispatch retry scheduler execution authorization 消费方时，优先读取 `child_executor_dispatch_retry_scheduler_binding_gate.retry_scheduler_execution_authorization` 或 `runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage`，确认 explicit authorization、production scheduler gate、durable schedule state、idempotency/dedupe、audit timeline、worker ownership 与 bounded attempts 均已进入 dry-run gate；不要把 dry-run ready 解释为 retry 已调度、durable schedule 已写入、worker 已启动或默认 scheduler 已启用。
- 新增 sandbox worker backend 消费方时，优先读取 `runtime_contract_summary.child_executor_sandbox_backend_coverage` 与 backend registry evidence，确认 adapter contract、guard、audit、idempotency、unsafe payload fail-closed、compact attempt evidence 与 opt-in execution seam success / blocked / failed paths 均已进入门禁；不要把 coverage 健康误解释为默认可启动 worker、queue、sandbox runtime、parent merge、retry scheduler 或 production dispatch。
- 新增恢复消费方时，优先读取 `run_recovery` dedicated contract，不直接从 SDK metadata 或 probe event 样本推断恢复状态。
- 新增恢复审计消费方时，优先读取 `run_recovery.latest_recovery_operation / run_recovery.recovery_operation_history / recovery_failed_closed.recovery_operation`；默认 `worker_ownership.implemented = false` 只表示恢复操作审计，不表示 worker lease 或跨实例所有权已实现。只有显式传入 ownership evidence 的 operation record 才能解释为“该次恢复尝试带有 worker lease 证据”。
- 下一刀 worker ownership 已完成 production gate contract、durable recovery gate evidence linkage、renewal supervisor readiness contract、renew-once opt-in execution seam、controlled renewal lifecycle、rollout readiness/operationalization/confirmation decision record/input source contract、auto-claim policy readiness contract、auto-claim entrypoint allowlist contract、explicit auto-claim enablement gate、SDK opt-in auto-claim gate enforcement、production enablement strategy contract、production default enablement input source、vendor lock adapter seam、PostgreSQL advisory lock probe contract、PostgreSQL advisory lock opt-in execution seam 与 runtime contract smoke / Quality Gate / Runtime Contract Gate 覆盖；后续若继续推进，应优先把 PostgreSQL seam 接入受控 rollout artifact 或实现 production enablement runtime config consumer，而不是把 strict SQL row lease/fencing、adapter seam readiness、PostgreSQL opt-in execution、rollout evidence、allowlist readiness、enablement gate readiness 或 opt-in lifecycle 直接视为默认生产授权。
- 下一刀 retry recovery 已从 compact evidence 推进到显式 opt-in scheduler seam；后续若继续推进生产级自动 retry，必须先实现 `recovery-retry-production-scheduler-gate` 的 durable state、idempotency/dedupe、backoff、terminal classifier、worker ownership、audit timeline、entrypoint allowlist 与 bounded attempts 检查，而不是把 opt-in seam 直接升级为默认后台自动重试。
- 后续若把 recovery audit trace writer 接入 SDK 主流程，应保持 opt-in / fail-open 语义，并继续复用 operation idempotency/dedupe 信息，不应让 Governance Timeline 自行扫描 SDK metadata；audit readiness 已可作为 production gate evidence，但不能替代 worker lease validation 或恢复执行授权。
- 新增默认 runtime 构造路径时，优先复用 `EmbeddedRuntimeFactory`，不继续在 SDK / Facade / Service 各自 new 默认依赖。
- 新增持久化姿态消费方时，优先读取 `persistence_interface`；`durable_ready` 只能表示 storage candidate，不能绕过 checkpoint / cursor / registry binding 的单 run 恢复 gate。
- 优先继续收 child intent taxonomy 与 parent merge contract，不先扩更多展示面。
- 下一刀 child executor 方向再评估是否需要把不同 intent 的 parent merge 结果进一步拆到更明确的 intent-specific sections；默认不扩一块新的通用展示面。
  - Child executor explicit executor binding opt-in 已补齐：preflight / execution prerequisites 会把 `explicit_executor_binding_opt_in` 作为真实执行前置要求，record-only binding 不再能被误读为 executor authorization；dispatch contract 也会暴露 explicit binding status/source/backend evidence，缺失 opt-in 时保持 blocked 且 `will_dispatch = false`。该能力只允许显式 opt-in skeleton execution 进入测试路径，不启动 worker、queue、sandbox runtime 或远端 executor。
  - Child executor dispatch attempt handoff contract 已补齐：`child_executor_dispatch_contract` 嵌套暴露 `child_executor_dispatch_attempt_handoff`，runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot 已覆盖默认 blocked、opt-in sandbox attempt envelope-ready 与 unsafe payload guard fail-closed。该能力仍不启用 dispatcher，不启动 worker、queue、sandbox runtime 或远端 executor。
  - Child executor sandbox dispatch-ready opt-in contract 已补齐：`build_child_executor_dispatch_contract(...)` 现在可在显式 sandbox backend binding、sandbox execution seam、child run payload 与 idempotency evidence 全 ready 时报告 `dispatch_ready = true` / `sandbox_dispatch_ready_opt_in = true`，同时固定 `will_dispatch = false` 并证明 backend adapter 未被调用；missing idempotency 与 unsafe payload 会 fail-closed。runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot / Health 归一化已覆盖 `opt_in_ready_dispatch_status / opt_in_ready_dispatch_ready / opt_in_ready_handoff_ready / opt_in_ready_will_dispatch`，该能力仍不启动 worker、queue、sandbox runtime 或远端 executor。
- Child executor dispatch result handoff contract 已补齐：dispatcher adapter 返回后的 compact result handoff / audit evidence 已可机器读取，并通过 runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot 覆盖 ready、blocked 与 malformed 三类路径。该能力仍不执行 parent merge、不调度 retry、不默认启用 worker。
- Child executor dispatch result retry audit policy 已补齐：result handoff 之后的 retry posture 已可机器读取，并通过 runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot 覆盖 no-retry、retryable、terminal 与 missing-idempotency blocked 路径。该能力仍不调度 retry、不默认启用 worker。
- Child executor dispatch retry scheduler handoff gate 已补齐：retry audit policy 到未来 retry scheduler 的只读 handoff 边界已可机器读取，并通过 runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot 覆盖 retryable-without-scheduler、missing-idempotency、missing-audit、terminal 与 bound-no-schedule 路径。该能力仍不调度 retry、不默认启用 worker。
- Child executor dispatch retry scheduler execution authorization dry-run 已补齐：binding gate 到未来 scheduler execution authorization 的只读授权审查边界已可机器读取，并通过 runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot 覆盖 default blocked、ready-but-no-schedule、production-gate-blocked、missing-durable-schedule、missing-audit/idempotency 与 missing-worker/bounded-attempt 路径。该能力仍不调度 retry、不写 durable schedule、不默认启用 worker。
- 再下一刀若继续推进 child executor，应优先评估 scheduler execution seam / durable schedule writer 的更窄 opt-in contract，或真实 sandbox backend adapter binding 的生产约束；不要默认启用 worker 或 retry scheduler。

是否继续优化：

- 是

停止条件：

- SDK 不再只依赖进程内存才能完成关键恢复路径。
- 垂域项目能以更稳定的方式把底座嵌进去，而不是只做 demo 接入。
- `II-1` 第一刀的边界说明、descriptor seam 和恢复 gate 已全部明确，后续实现不再边做边改语义。

### II-1 第一刀收束结论

当前建议将 `II-1` 第一刀视为**边界收口已完成、实现扩展待后续继续**，原因如下：

1. SDK 当前易失状态边界已被写清。
2. continuation descriptor 的结构与状态更新路径已统一。
3. `resume_run(..., continue_loop=True)` 与 `delegate_run(...)` 的恢复上限已被明确界定。
4. `workspace_store` seam 已落地，说明下一步可以真正进入 durable backend / cross-process recovery 实现，而不是继续只写边界文档。
5. recovery probe 与 fail-closed 结果 contract 已可运行，说明 II-1 已经不只是“有 seam”，而是开始进入正式恢复协议实现。
6. registry-backed continuation reattach 已落地，说明 II-1 已开始具备“descriptor -> executable continuation”的受控重挂能力，但仍未进入通用跨进程加载器阶段。
7. continuation binding catalog 已落地，说明后续 child executor / worker preflight / 运维排障已经有统一 binding 真源可依赖。

因此，后续如果继续推进 `II-1`，应进入真正的持久化与恢复实现，而不是继续反复补边界说明。

### Runtime Harness 参考对标补充

当前建议把外部参考源分成两类来使用，而不是混在一起：

1. `D:\AI\AIcode\learn-claude-code`
   - 主要用于校正 harness 概念分层、演化顺序和术语边界
   - 优先参考：`error recovery`、`runtime task model`、`agent teams`、`team-task-lane model`

2. `D:\AI\AIcode\claude-code`
   - 主要用于参考真实控制面机制
   - 优先参考：`InProcessBackend`、`inProcessRunner`、`permissionSync`、`reconnection`

落地原则：

- 借模式，不借产品耦合
- 借分层，不借命名
- 所有吸收动作都应先落入我方 OpenSpec 任务，不直接照搬外部实现

这会直接影响下一步 `II-1.6 child executor preflight`：它应先引用明确的参考切面，再决定我们自己的 preflight contract，而不是直接从某个参考仓库迁一个执行器过来。

#### II-2：Governance Timeline 前端瘦身

目标：

- 把当前已经变得较大的治理前端继续拆小，降低维护成本。
- 让新增治理事件时，前端不再持续堆大组件。

完成定义：

- `GovernanceTimelinePanel` 保留数据加载、路由过滤和主编排。
- 事件卡、过滤器、workspace、remediation、snapshot command 等继续按职责拆开。

当前状态：

- 进行中

当前进度：

- 已完成：
  - filter / event card / main_chat query workspace 第一轮拆分
  - `GovernanceTimelineFocusSummaryGrid` 已从 `GovernanceTimelinePanel` 抽出，父组件继续保留数据加载、路由过滤、query/stage/dedupe 状态和 clipboard 编排，summary grid 只负责展示与 action emit。
- 进行中：
  - 更细的治理工作区组件拆分与边界稳定
- 未开始：
  - 后续 remediation / snapshot command 周边是否继续下沉的判断

下一步动作：

- 优先判断哪些区块已经适合继续下沉成独立组件。
- 避免 `GovernanceTimelinePanel` 再回到所有逻辑都往里堆的状态。

是否继续优化：

- 是

停止条件：

- 父组件只保留主编排职责。
- 新增治理功能不再默认修改巨型面板文件。

#### II-3：Runtime Surface Contract Assembler

目标：

- 把 `RuntimeSurfaceService` 从“聚合 everything 的大服务”继续推进成更清晰的 assembler/builder 模式。
- 让 contract 真源、读取逻辑和组装逻辑边界更稳定。

完成定义：

- `RuntimeSurfaceService.get_runtime_profile()` 对外 contract 保持稳定。
- 内部 builder / assembler 可以独立维护和测试。

当前状态：

- 进行中

当前进度：

- 已完成：
  - query detail / history / subagent summary 等 dedicated contract 已开始出现
  - `RuntimeSurfaceProfileAssembler` 已从 `runtime_surface_builders.py` 移入专用 `runtime_surface_profile_assembler.py`，`RuntimeSurfaceService.get_runtime_profile()` 继续作为稳定入口，对外 profile shape 不变。
  - `RuntimeSurfaceProfileContextAssembler` 已承接 profile request context、runtime scope 调用边界和 recovery target 推导，顶层 profile shell 不再内联这些作用域细节。
  - `RuntimeCoreContractBuilder` 已承接 `runtime_core` 默认 shell、scope overlay、`child_display_id` fallback 与 child merge evidence 组装，`RuntimeSurfaceService._build_runtime_core_contract()` 保持兼容 wrapper。
  - Runtime Surface governance run-state fixture 已与 child executor explicit opt-in prerequisites 对齐，`risk_review` child merge semantics 不再因 blocked skeleton execution 回退为 `general_analysis`。
- 进行中：
  - 正式 builder / assembler 拆分
- 未开始：
  - governance overview 等更深 concern-specific builder 拆分与测试收口

下一步动作：

- 继续优先选择低副作用的 contract section 做 builder 拆分，下一步可评估 governance overview shell。
- 避免触碰 child executor replay、recovery scheduler 等高风险行为面，除非另开 OpenSpec change 并补足 focused smoke。

是否继续优化：

- 是

停止条件：

- Runtime Surface 的主要 contract 组装逻辑不再全部耦合在一个大服务里。

#### II-4：Phase II Exit Gate

目标：

- 给 `Phase II` 自己也补一个明确退出条件，避免恢复实现后再次无限膨胀。

完成定义：

- 能明确回答：什么时候继续恢复别的实现，什么时候重新回到高层边界层。

当前状态：

- 未开始

当前进度：

- 已完成：
  - `Phase I` 已有明确 exit gate
- 进行中：
  - 无
- 未开始：
  - `Phase II` 的正式 exit gate

下一步动作：

- 明确：
  - 何时允许重新开启新的 channel 推广实现
  - 何时必须暂停实现，回到规格/架构层

是否继续优化：

- 是

停止条件：

- `Phase II` 不会再因为“实现 momentum 很强”而无限拉长。

### Phase II 启动条件

- `Phase I` 的四个高层任务已完成。
- `query-run-read-model`、`query-workspace-generalization`、`channel-promotion-gate` 三份 canonical spec 已稳定存在。
- 当前明确不默认继续扩 `external_adapter recent summary`。
- 团队已同意把主注意力切回底座主线，而不是继续补 `main_chat` 局部体验。

### Phase II 推荐优先顺序

1. `II-1 Embedded SDK 持久化与恢复能力`
2. `II-2 Governance Timeline 前端瘦身`
3. `II-3 Runtime Surface Contract Assembler`
4. `II-4 Phase II Exit Gate`

### Phase II 暂缓事项

- 默认不继续新增 `main_chat` 局部治理体验增强
- 默认不立即恢复 `external_adapter recent summary` 对称试点
- 默认不推进任何 channel 的 `query detail / query history / query workspace` 新扩展

### Phase II 收束标准

- SDK 恢复与持久化能力进入下一成熟度层级。
- 治理前端拆分出更稳定边界。
- Runtime Surface assembler 思路明确并开始落地。
- 团队可以清楚判断：何时再回到 channel 级实现，何时继续留在底座主线。

### 继续优化判断规则

- 如果改动只是让已有卡片更漂亮、字段更多、筛选更细，但不提升 runtime core、read model 或 contract 一致性，则降级优先级。
- 如果改动会把前端推导逻辑继续做厚，而不是让后端 contract 更稳定，则默认不做，除非是短期验证。
- 如果一个方向连续 2 轮都只新增展示层价值、没有新增运行时收口价值，则必须暂停，重新回到阶段目标审查。

## 2. P0：文档入口产品化

目标：

- 让后续维护者不需要通读 `docs/change` 就能理解当前架构。
- 让垂域项目知道从哪些 seam 接入。
- 让阶段日志继续保留审计价值，但不再承担 onboarding 主入口。

当前落点：

- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/architecture/extension_points.md`
- `docs/roadmap/next_phase_hardening.md`

验收标准：

- `docs/README.md` 能直接引导到当前架构入口。
- 架构入口能回答“系统现在是什么、contract 在哪、怎么扩展、下一步做什么”。

## 3. P1：Embedded SDK 最小闭环

目标：

- 把 `EmbeddedAgentRuntimeSDK` 从 preview memory runtime 推进到更接近业务可嵌入的版本。
- 把 `AgentHarnessFacade` 从最小 run / stream / approve / resume / delegate / create_artifact / list_artifacts / execute 入口推进到支持持久化 workspace、真实 child executor、ToolRuntimeService / ApprovalEngine 集成、LLM reflector/reviewer、复杂 retry / model degrade policy 的默认 harness 体验。
- 支撑任意垂域 Python 项目以库的方式接入 Runtime Core。

已完成第一刀：

- `create_run`
- `stream_events`
- `submit_approval`
- `execute_run` 最小状态循环
- tool policy callable 与 `waiting_approval` 暂停 seam
- tool policy `approval_required` 到正式 `ApprovalRequestState` 的 SDK 闭环
- approved approval 到内存态 tool continuation 的恢复执行闭环
- denied approval 丢弃 pending tool continuation 的安全边界
- `resume_run(..., continue_loop=True)` 接回 observing / finalizing / done 后续 loop continuation
- run metadata 中可观测 `tool_approval_continuation` / `loop_continuation` descriptor
- continuation 生命周期 status event：`registered / consumed / discarded`
- Embedded SDK contract 暴露 `event_status_kinds`，让治理台和审计服务可发现事件面
- Runtime contract snapshot 已守护 `command_contract.embedded_sdk.event_status_kinds`
- Runtime contract snapshot 已校验 approval / done / continuation 必需 status_kind 枚举
- Runtime contract snapshot 已校验关键 SDK event 的 `required_payload`，防止事件名保留但 payload 字段静默漂移
- Embedded SDK 已提供 `validate_embedded_sdk_event_payloads(...)`，可校验真实事件样本是否满足声明的 required payload
- Runtime contract smoke 已新增 `embedded_sdk_event_payloads` 检查项，同时守护 profile contract 与真实 SDK event sample
- Quality gate report 已抽取 smoke JSON `checks`，并在 summary 中展示 Runtime Contract Checks，方便 CI artifact 和后续治理台读取
- Quality gate report 已支持从 Windows `quality_gate_smoke.ps1` 的混合 stdout 中抽取 `runtime_contract_smoke.py` JSON，避免 conda / PowerShell 包装输出导致 contract checks 丢失
- Quality gate report 已新增 `runtime_contract_summary`，聚合 Runtime Contract Checks 的整体状态、失败数、payload 缺口数与 approval replay/ignored 样本覆盖情况
- Quality gate report 已新增 `approved_tool_execution_coverage`，从 `runtime_approved_tool_execution_bridge` check 聚合 approved ask-tool continuation 与 deny override fail-closed 覆盖情况
- Quality gate report 生成 `runtime_contract_summary` 时已对 `embedded_sdk_event_payloads.missing_payload_count` 做 fail-closed 归一化，避免脏 smoke JSON 导致 artifact 生成失败
- Quality gate report 抽取和渲染 `contract_checks` 时已忽略非对象 check，同时保留原始 `structured_output` 作为排障证据
- Quality gate report 渲染 Markdown summary 时已忽略非对象 `runtime_contract_summary`，避免旧报告或手工报告破坏摘要渲染
- Quality gate report 渲染 Markdown summary 时已忽略非对象 step，避免旧报告或手工报告破坏主表、失败列表和 runtime contract 表格
- Quality gate report 渲染 Markdown summary 时已把非 list 的 `steps / failed_steps` 按空列表处理，避免旧报告或手工报告顶层类型漂移导致 TypeError
- Quality gate report 渲染 object step 时已容忍 `name / passed / exit_code / duration_seconds` 缺失，避免字段裁剪后的旧报告破坏 Markdown summary
- Quality gate report 渲染顶层报告字段时已容忍 `passed / step_count / failed_steps / steps` 缺失，避免旧报告或手工报告无法生成 Markdown summary
- Quality gate report 渲染旧报告或手工报告时，顶层 `failed_steps` 缺失会从 `passed = false` 的有效 steps 推导，避免失败数与主表冲突
- Quality gate report 渲染 `passed` 状态时已 fail-closed 归一化，避免字符串 `"false"` 被 Python truthiness 误渲染为 PASS
- Quality gate report 渲染 Markdown summary 表格时已转义 `|` 并折叠换行，避免失败原因或 summary 字段自由文本破坏 Runtime Contract Checks / Summary 表格
- Quality gate report 已新增 `runtime_contract_artifact_schema`，在 artifact 生成层守护 `runtime_contract_summary` 关键字段，尤其是 `subagent_lane_query_detail_coverage.detail_smoke`，并在 Markdown summary 中展示 schema guard
- Runtime Surface 后端 profile 已新增 `runtime_contract_gate`，可读取最近一次质量门禁报告中的 `contract_checks` 与 `runtime_contract_summary` 健康摘要
- Runtime Contract Snapshot 已把 `runtime_contract_gate.runtime_contract_summary` 纳入稳定字段守护，避免质量门禁摘要在后续 profile 改造中静默丢失
- Runtime Contract Snapshot 已进一步守护 `runtime_contract_summary` 内部关键字段，尤其是 `subagent_lane_query_detail_coverage.detail_smoke`，避免后端 profile 保留 summary 外壳但丢失门禁 coverage 信号
- Runtime Contract Gate 已暴露 `runtime_contract_artifact_schema`，新 artifact 直接读取 guard，旧 artifact 可从归一化 summary 派生，缺报告或缺 checks 时状态保持 `unknown`
- Runtime Contract Snapshot 已守护 `runtime_contract_gate.runtime_contract_artifact_schema` 的关键字段，完成 artifact 生成、Gate 暴露、Snapshot 防漂移三层后端闭环
- Runtime Contract Gate 在质量门禁报告缺失或 contract checks 缺失时，`runtime_contract_summary.overall_status` 会保持 `unknown`，避免把“未知”误解释为“已退化”
- Runtime Contract Gate 读取质量门禁 artifact 时已把非 list 的 `steps / contract_checks` 按空列表处理，避免旧报告、手工报告或截断字段拖垮 Runtime Profile
- Quality gate report 与 Runtime Contract Gate 读取 `observed_status_kinds` 时已只接受 list，避免字符串被误拆为字符集合或数字字段中断 Runtime Profile
- Quality gate report 渲染 Runtime Contract Summary 表格时已把非 object 的 `approval_replay_coverage` 按缺失处理，避免旧报告或手工报告中断 Markdown summary 生成
- Quality gate report 与 Runtime Contract Gate 读取 `approval_replay_coverage.event_payload_sample` 时已采用 fail-closed 布尔语义，避免字符串 `"false"` 被误判为已覆盖
- Runtime recovery approval kernel 已将 resolved approval 的 recovery entrypoint `recovery_reason` 收口为 `already_resolved`，让 SDK probe 与 Runtime Surface recovery 使用同一套机器可读 reason
- Runtime contract smoke 已新增 `approval_lifecycle_recovery_alignment` check，覆盖 approved replay、denied reversal ignored 与 resolved recovery gate 对齐
- Quality gate report 与 Runtime Contract Gate 已将 `approval_lifecycle_recovery_alignment` 归一化为 `runtime_contract_summary.approval_lifecycle_recovery_coverage`，并由 Snapshot / artifact schema 守护 `alignment_smoke`
- Quality gate report 渲染 Markdown summary 时已对 `Approval Lifecycle Recovery` 列做严格证据校验，避免手工或旧 artifact 只写 `alignment_smoke=true` 就显示为已覆盖
- Runtime Contract Gate 与 degraded trace 会对 `approval_lifecycle_recovery_coverage` 做严格证据校验；`alignment_smoke=true` 但 replay/ignored/recovery reason 不匹配时会 fail-closed 为未覆盖
- Runtime contract smoke 已新增 `runtime_approved_tool_execution_bridge` check，覆盖 facade + ToolRuntimeService 的 approved ask-tool continuation 执行，以及 deny override fail-closed
- Runtime contract smoke 的 `runtime_profile_contract_snapshot` check 已输出 artifact schema guard 证据字段，quality gate artifact 可直接看到 schema guard 状态和缺失字段
- Runtime Contract Gate 已归一化 `runtime_contract_summary.approved_tool_execution_coverage`；旧报告或缺失 bridge check 会 fail-closed 显示 `bridge_smoke = false`
- Runtime contract smoke 已新增 `subagent_lane_query_detail` check，`quality_gate_report.py` 与 Runtime Contract Gate 已归一化 `runtime_contract_summary.subagent_lane_query_detail_coverage`；旧报告或缺失 detail check 会 fail-closed 显示 `detail_smoke = false`
- Runtime contract smoke 已新增 `worker_ownership_store_mode` check，`quality_gate_report.py` 与 Runtime Contract Gate 已归一化 `runtime_contract_summary.worker_ownership_store_mode_coverage`；旧报告或证据缺失会 fail-closed 显示 `mode_smoke = false`
- Runtime contract smoke 已新增 `recovery_retry_evidence` check，`quality_gate_report.py` 与 Runtime Contract Gate 已归一化 `runtime_contract_summary.recovery_retry_evidence_coverage`；旧报告、缺失 check 或证据不完整会 fail-closed 显示 `retry_smoke = false`，并且该覆盖只证明 compact retry evidence，不表示自动 retry execution / scheduler 已实现
- Recovery retry evidence smoke 已与 classifier 语义对齐：`workspace_backend_not_durable` 作为 fail-closed 样本会保持 `retryable = false`，但 exhausted evidence 仍可在保留 terminal、attempt bounds、recovery reason 与 idempotency key 时被 quality gate 视为覆盖。
- Runtime contract smoke 已新增 `child_executor_promotion_gate` check，`quality_gate_report.py` 与 Runtime Contract Gate 已归一化 `runtime_contract_summary.child_executor_promotion_gate_coverage`；旧报告或证据缺失会 fail-closed 显示 `gate_smoke = false`
- Embedded workspace backend 已新增 `state_contract`，用同一份机器可读词表区分 durable state 与 runtime-only state，为后续 checkpoint / resume cursor 收口提供边界
- Embedded SDK recovery probe 已新增 `checkpoint` 与 `resume_cursor` 第一刀：durable workspace + registry binding 可形成 `checkpoint.status = ready` 与 `resume_cursor.cursor_status = ready`；非 durable workspace、缺 binding、approved/denied resolved approval 会分别进入 blocked/stale 的机器可读状态。
- Embedded SDK 已新增 recovery operation evidence 第一刀：registry reattach 成功会在 run metadata 中记录 `operation_status = recovered`，fail-closed 恢复事件会携带 `operation_status = blocked`，并显式声明 worker ownership / lease 未实现。
- Runtime Surface `run_recovery` 与 Governance Overview 的 `run_recovery` 摘要已透出 checkpoint/cursor 字段，恢复消费方不再需要从 continuation descriptor 反推“现在能否恢复到哪个入口”。
- Runtime contract smoke 已新增 `durable_checkpoint_resume_cursor` check，Quality Gate / Runtime Contract Gate / Snapshot 已归一化并守护 `runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke`。
- Runtime Contract Gate degraded trace detail 已新增 `checkpoint_cursor=<covered|missing|unknown>`，checkpoint/cursor coverage 变化会随 summary 进入 fingerprint / dedupe key。
- Runtime Contract Gate degraded trace detail 已新增 `recovery_retry=<covered|missing|unknown>`，recovery retry evidence coverage 会随 summary 进入 payload / fingerprint / dedupe key；该治理信号仍只代表显式 retry evidence 覆盖，不代表自动 retry scheduler 已实现。
- Recovery retry 已有显式 opt-in scheduler seam，并新增 production scheduler gate contract；`production_automatic_retry=True` 会在 gate blocked 时 fail-closed，不会启动后台或默认自动重试。默认后台重试必须等 durable scheduling state、worker ownership 和 audit/dedupe 证据完整后再开启。
- Embedded SDK `register_tool(...)` 已从 draft boundary 推进为 ToolRuntimeService bridge：SDK 调用方可以注册 ToolSpec 元数据和可选 executable handler，并复用同一份 tool runtime registry。
- Embedded SDK `execute_run(...)` 已在未传入显式 `tool_executor` 时复用 ToolRuntimeService 默认执行桥接；SDK-only 集成现在可以完成 register -> policy -> approval/fail-closed -> execute 的最小闭环。
- SDK 直连 ToolRuntimeService 执行桥已进入 `runtime_contract_smoke.py` 与质量门禁摘要；`sdk_tool_runtime_execution_bridge` 会覆盖 auto、ask-approved 与 deny fail-closed 三条路径，并汇总为 `runtime_contract_summary.sdk_tool_runtime_execution_coverage`。
- ToolRuntime timeout/retry contract 已进入 runtime contract smoke、Quality Gate、Runtime Contract Gate 与 Snapshot 守护；`tool_runtime_timeout_retry` 会覆盖 recovered retry、exhausted retry 与 post-call elapsed timeout metadata，并汇总为 `runtime_contract_summary.tool_runtime_timeout_retry_coverage`。该覆盖只证明同步 retry / elapsed timeout 元数据，不表示 hard cancellation、sandbox execution 或 worker-level timeout 已实现。
- Embedded SDK reviewer / fallback 事件已进入 `event_status_kinds.required_payload`：review approved/rejected 与 fallback handled/fail-closed 现在可通过真实 SDK event sample 做 payload validation，默认仍不接真实 LLM、不改变 `/api/chat`。
- Runtime Contract Gate 读取质量门禁 artifact 时已对 `runtime_contract_summary` 与 `contract_checks` 计数字段做 fail-closed 归一化；不可解析或负数会回退到推导值或 `None`，避免脏 artifact 拖垮 Runtime Profile
- Runtime Surface 前端治理台已新增 `Contract Gate` 卡片，展示质量门禁契约检查的整体状态、失败数和 checks 明细
- Runtime Surface 前端 `Contract Gate` 卡片已展示 `runtime_contract_summary`，可直接看到 payload 缺口与 approval replay/ignored 样本覆盖情况
- Runtime Surface 顶部摘要已新增 `契约门禁` 信号，让质量门禁退化能在入口第一屏被发现
- Runtime Surface 顶部 `契约门禁` 已可跳转 Governance Timeline 的 `runtime_contract + warning` 过滤视图
- Runtime Profile 带上下文读取时，已能把 degraded `runtime_contract_gate` 记录为 `runtime_contract_gate_degraded` trace
- Runtime Contract Gate degraded trace payload 已携带 `runtime_contract_summary`，并把 payload 缺口、approval replay/ignored 覆盖状态与 approved tool bridge 覆盖状态纳入 fingerprint 去重签名
- Runtime Contract Gate degraded trace detail 已新增 `approval_lifecycle=<covered|missing|unknown>`，让 compact 治理事件摘要可直接看到审批生命周期恢复覆盖状态
- Runtime Contract Gate degraded trace payload 已归一化 `approval_lifecycle_recovery_coverage`，审批生命周期恢复对齐覆盖状态变化会生成新的 fingerprint / dedupe key
- Runtime Contract Gate degraded trace payload 已归一化 `approved_tool_execution_coverage`，coverage 从缺失变为已覆盖时会生成新的 fingerprint / dedupe key，而不是被旧 trace 误去重
- Runtime Contract Gate degraded trace payload 已归一化 `recovery_retry_evidence_coverage`，retry evidence coverage 从缺失变为已覆盖时会生成新的 fingerprint / dedupe key，而不是被旧 trace 误去重
- Runtime Contract Gate degraded trace payload 已归一化 `subagent_lane_query_detail_coverage`，detail smoke coverage 从缺失变为已覆盖时会生成新的 fingerprint / dedupe key，而不是被旧 trace 误去重
- Runtime Contract Gate degraded trace payload 已归一化 `runtime_contract_artifact_schema`，artifact schema guard 状态或缺失字段变化会生成新的 fingerprint / dedupe key
- Governance Timeline 已把 `runtime_contract_gate_degraded.payload.runtime_contract_summary` 渲染为轻量摘要，排查时无需展开完整 Payload 即可看到 payload 缺口、approval replay 覆盖状态与 `subagent_detail=<covered|missing|unknown>`
- Runtime Contract Gate degraded trace 已增加 fingerprint 去重，避免 Runtime Surface 刷新重复污染 Governance Timeline
- Runtime Contract Gate trace payload 已持久化 fingerprint，并可基于历史 trace 识别重复 degraded 事件
- Runtime Contract Gate trace 已标准化 `dedupe_key`，为后续唯一索引或跨实例强一致去重预留稳定 contract
- RunTraceService 已抽出通用 `has_runtime_trace_dedupe_key(...)` seam，后续治理事件可复用同一幂等查询能力
- Doctor `doctor_gate_failed` 已接入通用 `dedupe_key` seam，避免重复门禁失败污染 Governance Timeline
- Framework Adapter `framework_adapter_precheck_completed` 已接入通用 `dedupe_key` seam，避免重复预检污染 Governance Timeline
- Framework Adapter `framework_adapter_external_error` 已接入通用 `dedupe_key` seam，避免重复外部运行失败污染 Governance Timeline
- Governance Timeline 事件卡片已展示 payload `dedupe_key` 预览，让治理幂等状态可在前端直接观察
- Governance Timeline 事件卡片已支持复制完整 `dedupe_key`，方便排查重复事件和跨 trace 比对
- Governance Timeline 已支持 `governance_dedupe_key` 路由聚焦，复制当前视图时会带上幂等键，便于治理视图精确回放
- Governance Timeline 已支持幂等键聚焦 summary 与一键清除，便于从精确事件视图回到同一治理域的完整事件集合
- Governance Timeline 已支持幂等键聚焦空状态，复制链接过期或 key 不匹配时会显示原因并提供清除入口
- Governance Timeline 事件卡片已支持 `聚焦幂等键`，可从单个事件直接进入 `governance_dedupe_key` 精确过滤视图
- Governance Timeline 事件卡片已支持 `已聚焦幂等键` 禁用态，明确当前事件是否命中正在生效的幂等键过滤
- Governance Timeline 幂等键聚焦 summary 已支持复制当前 active `dedupe_key`，方便从路由聚焦视图继续流转 issue/CI 排查
- Governance Timeline 已在 active `dedupe_key` 切换时重置 summary 复制态，避免旧 key 的“已复制”状态污染新聚焦视图
- Governance Timeline 幂等键聚焦 summary 已显示匹配事件数，明确当前 key 在过滤范围内的命中比例
- Governance Timeline 复制当前视图已包含幂等键匹配数，便于 issue/CI artifact 离线判断重复事件规模
- Governance Timeline 事件卡片的 `dedupe_key` 预览已改为中间截断，保留前缀签名和尾部错误详情
- Governance Timeline 事件卡片的 `dedupe_key` 预览已通过 `title` / `aria-label` 暴露完整 key
- Governance Timeline 幂等键聚焦 summary 的截断预览已通过 `title` / `aria-label` 暴露完整 active key
- Governance Timeline 事件卡片的 `聚焦幂等键` / `已聚焦幂等键` 按钮已通过 `title` / `aria-label` 暴露完整 key
- Governance Timeline 事件卡片的 `复制幂等键` / `已复制幂等键` 按钮已通过 `title` / `aria-label` 暴露完整 key
- Governance Timeline 幂等键聚焦 summary 的 `复制当前幂等键` / `清除幂等键` 按钮已通过 `title` / `aria-label` 暴露完整 active key
- Governance Timeline 幂等键聚焦空状态的 `清除幂等键聚焦` 按钮已通过 `title` / `aria-label` 暴露完整 active key
- Governance Timeline 幂等键聚焦空状态的 active key 文本已通过 `.timeline-empty-dedupe-key`、`title` 与 `aria-label` 暴露完整 key
- Governance Timeline 幂等键聚焦 summary 的匹配数已通过 `.dedupe-focus-match-count` 与 `aria-label` 暴露为稳定可观测节点
- Governance Timeline Framework Adapter 错误类型 summary 的 `清除错误类型` 按钮已通过 `title` / `aria-label` 暴露当前 error type
- Governance Timeline Framework Adapter 错误类型 summary 的展示值已通过 `.framework-error-type-focus-label`、`title` 与 `aria-label` 暴露当前 error type
- Governance Timeline `风险模式` summary 的展示值已通过 `.severity-focus-label`、`title` 与 `aria-label` 暴露当前 severity
- Governance Timeline `当前筛选` summary 的展示值已通过 `.filter-focus-label`、`title` 与 `aria-label` 暴露当前 governance filter
- Governance Timeline `当前计划` / `聚焦步骤` summary 的展示值已通过 `.plan-objective-label` / `.focus-step-label`、`title` 与 `aria-label` 暴露当前上下文
- Governance Timeline `审计事件` / `运行 Trace` summary 计数已通过 `.audit-count-label` / `.trace-count-label`、`title` 与 `aria-label` 暴露当前数量
- PolicyEngine 到 Execution Loop 的 `build_policy_engine_tool_policy(...)` adapter
- tool policy `denied` fail-closed 语义
- tool executor callable 与 tool event/history seam
- reflector callable 反思与 revise iteration
- reviewer callable 质量门禁
- fallback handler callable 降级 seam

建议下一刀：

- SDK approval lifecycle trace adapter 已完成第一刀：`approval_resolved / approval_replayed / approval_ignored / recovery_failed_closed` 可通过显式 recorder 进入 Runtime Trace，写入失败不影响 SDK approval/recovery 主流程。
- 后续若继续扩展 SDK governance recorder，应先评估是否需要把更多 SDK event 纳入同一 adapter；当前不建议直接把所有 SDK event 全量写入 Governance Timeline。
- `AgentHarnessFacade` 已新增最小 ToolSpec 注册与默认本地工具 executor bridge；`execute()` 未显式传入 tool executor 时，可复用已注册 handler，并把 action / observation metadata 写入 SDK-owned `tool_result.execution` 与 `run.tool_history`
- `EmbeddedAgentRuntimeSDK.register_tool(...)` 已接入 ToolRuntimeService registry，避免 SDK 用户绕开 facade 时只能停在未实现 draft boundary。
- `EmbeddedAgentRuntimeSDK.execute_run(...)` 已接入 ToolRuntimeService 默认 executor bridge；当 tool policy 给出 allowed 决策时，SDK 会先 probe ToolRuntimeService permission gate，再把 ask/deny 映射回 SDK-owned approval/fail-closed 状态机。
- `ToolRuntimeService` 已新增最小 `execute_tool(...)` adapter，Facade 在无本地 handler 时可通过 ToolRuntimeService 执行 registry tool，并保持 SDK-owned event / history trace；当前支持 `permission_level_gate_v1` policy coordination、required args 校验、同步异常 retry 和 post-call elapsed timeout metadata，sandbox / worker 级硬超时仍是后续 contract 边界
- `ToolRuntimeService` schema validation 已从 required args 提升到 lightweight schema v1，当前覆盖 `required / type / enum / object.required`，仍不引入完整 JSON Schema 依赖或 coercion
- `ToolRuntimeService.execute_tool(...)` 现在会先把 `permission_level` 映射为 `allowed / approval_required / denied`；`ask / high_risk` 在执行前返回 `approval_required`，`deny` 在执行前返回 `policy_denied`，但 approval request 的创建和生命周期仍归 `ApprovalEngineService / EmbeddedAgentRuntimeSDK` 管
- `AgentHarnessFacade.execute(...)` 已桥接 `ToolRuntimeService.evaluate_tool_policy(...)`；当调用方的 tool policy 说 `allowed` 但 runtime ToolSpec 是 `ask / high_risk / deny` 时，facade 会在执行前改写成 SDK 的审批或拒绝状态，不再把 runtime-service 拦截结果当普通 tool result
- `EmbeddedAgentRuntimeSDK` 的 approved tool continuation 现在会给 facade runtime-service executor 提供临时 approved marker；ToolRuntimeService 只对原本 `approval_required` 的工具接受 approved override，审批通过后的 `ask / high_risk` 工具可恢复执行，`deny` 仍 fail-closed
- 上述 approved runtime-service tool execution 已进入 `runtime_contract_smoke.py`，quality gate artifact 可持续捕获 `approved_policy_original_status / approved_policy_override_status / deny_override_status`
- Query Control mapper 已新增 compact `tool_runtime_observation` read model，可把 tool result 的 policy / schema / retry / timeout 状态带入治理 trace payload，同时避免复制完整工具结果正文
- 继续评估 `ExecutionLoopController` 如何接入真实 LLM step、ToolRuntimeService、LLM reflector/reviewer、retry policy 和 model degrade policy。
- 继续推进 `ii3-durable-runtime-checkpoint-resume`：把当前 checkpoint/cursor probe 第一刀接入 runtime contract smoke、quality gate summary、Runtime Contract Gate 和 Snapshot 守护。
- 继续评估 `resume_run(..., continue_loop=True)` 是否需要支持更完整的持久化 continuation descriptor、跨进程恢复和失败重试；持久化姿态已由 `persistence_interface` 表达，不再新增平行 durable flag。
- 评估 tool continuation 是否需要持久化 descriptor，避免跨进程或服务重启后丢失待恢复工具。
- 评估 `delegate_run` 是否需要接入真实 child executor、独立上下文预算和结果 merge。
- Child Executor dispatch retry scheduler binding gate 已完成第一刀：retryable dispatch result 可以形成机器可读 scheduler binding decision gate，默认仍 blocked；即使 evidence ready 也保持 `will_schedule_retry=false`，不启动 worker、不调度 retry、不默认启用 scheduler。
- 后续若继续推进 child dispatch retry scheduler，应优先做显式 scheduler execution authorization / dry-run decision，而不是直接启用真实 worker 或 production scheduler。
- 评估下一刀是否推进真实 sandbox backend execution seam 或 child dispatch retry scheduler execution authorization；在此之前不要把 adapter contract ready 或 binding gate ready 误读为 production child executor dispatch ready。
- 评估 artifact 能力是否需要进一步接入 workspace path、跨进程 artifact index 和治理台 replay 面板。

暂缓：

- 完整远程 tool registry 执行、schema validation、沙箱隔离、超时与 retry。
- 多租户权限模型。
- 复杂远程部署 SDK。

验收标准：

- SDK 不绕过 approval / trace / policy。
- SDK 能创建 run 并读取事件。
- SDK contract 仍能出现在 Runtime Surface。

## 4. P1：Governance Timeline 前端瘦身

目标：

- 降低 `GovernanceTimelinePanel.vue` 的维护成本。
- 让后续新增治理事件不再继续堆大组件。
- 当前已完成 `main_chat` 查询历史/详情的工作区下沉，后续继续瘦身应优先沿 summary / action / workspace 边界拆分。
- 当前已完成治理 overview、基础 summary-action、Framework Adapter 专题卡与 remediation 卡的下沉；后续若继续拆分，应优先保持 `GovernanceTimelineEventStream` 作为主事件流主干，不建议再把事件流进一步碎片化。

建议拆分：

- `GovernanceTimelineFilters.vue`：已完成第一刀。
- `GovernanceTimelineEventCard.vue`：已完成第二刀。
- `GovernanceRemediationCard.vue`：可视为 `GovernanceTimelineFrameworkAdapterRemediationCard` 的后续演进方向。
- `GovernanceSnapshotCommandCard.vue`：当前已由 `GovernanceRecentSnapshotCommandsCard` 承担，不建议重复拆分。

验收标准：

- 父组件只保留数据加载、路由过滤、分页/刷新。
- 子组件只负责展示和事件透出。
- 现有 `GovernanceTimelinePanel.test.js` 通过。

## 5. P2：Runtime Surface 后端 contract assembler

目标：

- 让 `RuntimeSurfaceService` 更像编排层，而不是所有 contract 的直接构造者。

建议拆分：

- `RuntimeProfileAssembler`：已作为 `get_runtime_profile()` 的主组装入口落地。
- `RuntimeCoreContractBuilder`：已承接 `runtime_core` shell、scoped overlay 与 child merge evidence。
- `GovernanceOverviewRunStateBuilder`：已先承接 `governance_overview.run` 的 run-state assembly，作为完整 `GovernanceOverviewContractBuilder` 前的安全拆分点。
- `GovernanceOverviewContractBuilder`
- `ProviderCatalogBuilder`：已承接模型过滤、provider 汇总和 `provider_resolution` 组装，并有 focused 单测守护。

验收标准：

- `RuntimeSurfaceService.get_runtime_profile()` 保持对外 contract 不变。
- contract builder 可独立单测。
- `runtime_contract_snapshot_service.py` 仍能检测漂移。

## 6. P2：外部 Framework Adapter 扩展准备

目标：

- 在 LangGraph draft adapter 稳定后，为 DeepAgents / CrewAI 风格 adapter 留出清晰接入模板。

建议动作：

- 提取 adapter authoring checklist：已完成第一刀，`FrameworkAdapterRuntimeService.build_adapter_authoring_checklist(...)` 会输出 side-effect-free checklist / conservative promotion review，固定 identity、lifecycle mapping、readiness、governance timeline、promotion gate 和 non-goals。
- 为新 adapter 增加最小测试模板。
- 固定 readiness / precheck / pilot / execution gate 命名。

暂缓：

- 不要立刻把外部 adapter 接入主 chat。
- 不要为了覆盖多个框架提前抽象过度。
- checklist ready 不等于 adapter 已进入生产执行；`default_chat_entry` 仍固定为 `disabled`。

## 7. 当前不建议做的事

- Worker ownership 已新增 PostgreSQL vendor lock target artifact binding：同一 rollout artifact family 现在可只读生成 `target_decision_input` 与 `target_decision` evidence；默认仍不执行 advisory lock SQL、不启用 production lock、不解除 durable recovery 的 worker ownership / rollout blocker。
- Worker ownership 已新增 PostgreSQL vendor lock semantics binding：ready target artifact binding + opt-in execution seam 现在可形成 vendor lock semantics candidate；默认仍不执行 advisory lock SQL、不更新 production gate、不启用 production lock。
- Worker ownership 已新增 PostgreSQL vendor lock production gate wiring decision：ready semantics candidate 可被显式批准为 future production gate input；默认仍不更新 production gate、不启用 production lock、不执行 advisory lock SQL。
- Worker ownership 已新增 production gate composition dry-run：vendor lock wiring、renewal lifecycle、rollout confirmation、auto-claim enablement、audit 与 enablement input 可被组合评估为 ready dry-run；默认仍不启用 production default、不执行 lock、不启动后台 worker、不运行 recovery auto-claim。
- Worker ownership 已新增 production enablement runtime config consumer：完整 caller-owned config 可生成 ready enablement input 与 ready dry-run nested evidence；默认仍不读取外部配置、不修改环境、不启用 production default、不执行 lock、不启动后台 worker、不运行 recovery auto-claim。

- 不建议把项目迁到某个外部 harness 框架之上。
- 不建议重写 Runtime Core。
- 不建议把治理台做成完整业务后台。
- 不建议在没有真实垂域需求前做复杂多租户。
- 不建议让 LangGraph external pilot 直接进入主对话执行链。

## 8. 推荐执行顺序

当前推荐按“规格 -> 实现 -> 归档 -> git 提交”的节奏推进：

1. 规格：先确认是否影响 runtime contract、read model、治理语义或 framework adapter；命中则创建 OpenSpec change，并写清 adapter 边界、promotion gate、非目标和验证方式。
2. 实现：一次只推进一个最小可验证切片，优先保持 Runtime Core、ToolRuntime、Query Control 和 Governance contract 稳定。
3. 归档：实现完成后同步 canonical spec、architecture docs、roadmap，再把 change 归档到 `openspec/changes/archive/`。
4. git 提交：在验证结果、归档位置和后续项明确后再提交。

下一批优先级：

1. 完成文档入口产品化，并把 `agent-runtime-control-plane-positioning` 与 `agent-runtime-control-plane-entrypoint-readiness` 作为项目定位入口。
2. 准备 framework adapter authoring checklist / promotion gate，而不是直接接入第二个框架。
3. 深化 Embedded SDK 持久化与恢复能力。
4. 拆 Governance Timeline。
5. 拆 Runtime Surface contract assembler。

当前补充：

- Domain agent grounded-answer 证据链已经达到 repo-side minimal integration trial pack 完成线。后续除非真实调用方试接暴露具体缺口，否则不再默认沿 domain-agent evidence 继续拆小阶段。
- 默认下一步应回到 Agent Runtime Control Plane 入口、Embedded SDK / Execution Loop 主干，或 framework adapter authoring checklist，而不是继续增加本地 trial evidence 层。
