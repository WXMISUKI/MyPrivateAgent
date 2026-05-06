# MyPrivateAgent 简历 & HR 沟通话术

> 这份文档的目的：让你能在 3 分钟向 HR / 非技术面试官讲清楚项目是什么、为什么有价值、自己的贡献，并且在被追问"还有什么不足"时给出坦诚可信的回答。风格：技术务实、不吹不夸。

## 1. 一句话介绍（电梯间版）

> 我自研了一套参考 Claude Code 架构的通用智能体运行时框架。它不是一个 chatbot，而是为后续任意垂域 Agent 提供可复用的底座——主执行循环、多智能体调度、工具/Skill/MCP 三层能力面、权限与策略治理、可观测性全部自研并已收口。

## 2. 30 秒自我介绍（面向 HR）

> 我做了一个叫 MyPrivateAgent 的项目。它的定位是通用智能体框架的基座，不是具体的业务 Agent。我参考了 Anthropic 的 Claude Code 开源架构，用 FastAPI + Vue 3 从零搭建了完整的后端执行链、调度器、治理层、前端操作台。项目已经跑通主链路：从状态机、统一事件协议、父子执行模型、权限审批、工具/技能/MCP 三层能力、结构化卡片渲染、CI 质量门禁、到 Vercel 一体化部署。代码规模上，后端 21K 行、前端 13K 行、测试 8K 行、设计文档 20 多份。

## 3. 为什么这个项目对 HR 来说有说服力

不同于常见的"包一层 LangChain 做 demo"的项目，这套框架可以讲出三条差异化卖点：

### 3.1 从架构层动手，而不是只会调 API

- 项目里明确分了六层：Interface / Orchestration / Runtime Core / Governance / Capability / Infrastructure
- 运行时有显式状态机（`INIT → PLANNING → GENERATING → TOOL_CALLING → WAITING_APPROVAL → OBSERVING → MERGING → FINALIZING → DONE / FAILED / ABORTED`），非法迁移直接抛错
- 事件协议统一：`event_id / run_id / parent_run_id / conversation_id / iteration / type / payload`，任何一次执行都可按 run_id 回放
- 数据库有 20+ 张表，`PlanRunRecord / SchedulerRunRecord / ChildRunRecord / PermissionRequestRecord / ArtifactRecord / CapabilityRemediationRecord` 这些一等对象都是真正持久化的，不是 metadata 拼接

### 3.2 做了很多"企业级"才会关心的事

- **策略引擎**：高风险工具关键字阻断、子智能体工具白名单、provider 优先级
- **审批闭环**：`WAITING_PERMISSION` 状态暂停执行，前端审批通过后恢复
- **可观测性**：统一 run trace、Doctor 自检、QualityGate 报告（CI 中 upload artifact）
- **多智能体调度**：planner item fan-out 成多个 child run，child 有独立状态 `queued / running / completed / failed / cancelled`，失败时 provider 自动降级
- **能力缺口治理**：每次触发能力边界都落 trace，系统会聚合近期高频缺失能力并给出"建议补工具 / Skill / MCP"的方向

### 3.3 工程化不是空话

- CI 四个 job：backend-lint / backend-tests / quality-gate / frontend-build
- 40+ 个后端单测，涵盖 service / router / harness / runtime 各层
- 10+ 个 smoke 脚本：认证会话、SSE 流式、错误事件、停止生成、多智能体策略、provider 故障转移、能力缺口治理
- 文档不是一份 README 糊弄事，是 20+ 份带版本演进的设计稿：企业级总方案、目标架构、路线图、Claude 对齐改进、各子域建设计划
- 部署链路完整：本地 SQLite 零配置、MySQL 可无缝切换、Docker、Vercel 一体化都已跑通

## 4. 关键数字（被追问规模时说）

| 维度 | 数字 |
|---|---|
| 后端 Python 代码 | 约 21,000 行 |
| 后端 services 模块数 | 40+ 个领域服务 |
| 前端 Vue 代码 | 约 13,000 行 |
| 前端治理面板 | 10+ 个（Runtime Debug、Planner、Doctor、Governance Timeline、MCP、Provider、Capability Gap、Command Palette 等） |
| 测试代码 | 约 8,000 行，60+ 个测试文件 |
| 数据库表 | 20+ 张，3 个 Alembic 迁移版本 |
| 设计文档 | 20+ 份 |
| CI Jobs | 4 个（lint / tests / quality-gate / frontend-build） |
| Smoke 脚本 | 10+ 个 |
| 支持的 Provider | 火山引擎豆包 Ark、Ollama 本地模型，Anthropic / OpenAI 已抽象预留 |

## 5. 项目亮点清单（每条都对应真实可查的代码）

### 5.1 自研核心循环 AgentHarness

- 位置：`backend/harness/agent_harness.py`，约 1,800 行
- 解决的真实问题：豆包/OpenAI 兼容模型流式返回工具调用时按 index 分块，自研了 `StreamingToolCallTracker` 按 index 聚合参数、去重片段、容错解析 JSON（有 `json_repair` 兜底）
- 双模支持：`bind_tools` + 豆包原生 tool definitions 格式；检测到模型不支持工具时自动降级为纯文本解析
- 错误治理：`ErrorHandler` 把底层异常归一为 5 类（`provider_timeout / provider_connection / provider_rate_limit / provider_unavailable / tool_validation`），可重试的走指数退避，最大 60s
- 循环防抖：相似工具调用超过 2 次主动打断，避免死循环
- 最终合成模式：积累足够观察后切回原始模型做最终合成

### 5.2 父子执行模型（真正的多智能体调度）

- 位置：`backend/services/scheduler_service.py`、`subagent_service.py`、`subagent_registry_service.py`
- `planner item` 可 fan-out 成多个 `child run`，child 状态独立流转
- 子智能体按角色注册：`frontend / backend / qa / docs / planner`，每个角色有专属工具白名单和提示词
- `ChildRunRecord` 已升级为数据库一等对象，不再依赖 planner metadata
- Provider 失败时自动降级到下一家，有专门的 `ProviderFailoverAnalyticsService` 统计降级率

### 5.3 三层能力面 + 能力合同

- Tool 层：`ToolSpec` 统一元数据，含 `permission_level / deterministic / cache_ttl / render_mode / card_schema`
- Skill 层：frontmatter 契约，按 `triggers / agent_roles / required_capabilities / priority / activation_mode` 匹配
- MCP 层：Registry + Runtime + Session + Adapter 四件套，支持 stdio 和 http transport
- 每轮执行前，`CapabilityProfileService` 把三层合成为"运行时能力合同"写进 system prompt，明确告诉模型可用/受限/缺失能力

### 5.4 治理闭环

- `PolicyEngineService` 确定性前置判定
- `PermissionService` 持久化审批请求，前端审批后恢复执行
- `AgentHookService` 提供 `PreToolUse / PostToolUse / SessionStart / Stop` 钩子
- `RunTraceService` 是 chat / scheduler / subagent / policy / hook / mcp 的统一 trace 入口
- `DoctorRuntimeService` + `quality_gate_report.py` 持续做回归守门

### 5.5 前端不是"会聊天就完事"

- 10+ 个专门的治理面板，不是 demo-ware
- 结构化卡片协议：`AgentStructuredCard / WeatherCard / DateTimeCard / SearchSummaryCard`，走统一 `card_schema`
- 反馈打分闭环，数据库侧有 `uq_message_feedback_conv_msg_user` 唯一约束保证幂等

## 6. 可以跑给面试官看的演示路径

如果现场要演示，按这个顺序讲：

1. 先跑 `python scripts/doctor.py`，展示有完整环境自检
2. 启动后端 + 前端，在 demo_guest 模式下无需登录直接进入聊天
3. 问一个"上海今天天气"——走 weather tool，前端按 card schema 渲染成结构化卡片
4. 打开 **AgentRuntimeDebugPanel**，展示同一个 run 的状态机轨迹和事件流
5. 打开 **GovernanceTimelinePanel**，展示权限 / 策略 / 审批的治理时间线
6. 打开 **CapabilityGapSummaryPanel**，展示系统自动识别出的能力缺口及补强建议
7. 最后跑 `python scripts/chat_stream_smoke.py`，展示 CI 里同样的 smoke 可以一条命令端到端验证

## 7. 待完善项（面试时被问"还有什么不足"的标准答案）

**主动说这些比被问出来好 10 倍**，我提前列好，每条都有对应的文档佐证：

1. **类型化记忆还没落地**：当前 `AgentMemoryService` 偏文件加载层，缺 `user / feedback / project / reference` 四类语义与相关性召回评分（`claude_alignment_improvement_plan.md` 有规划）
2. **权限模型偏单层**：还没做组织 / 项目 / 用户三级策略覆盖，`ApprovalEngine` 作为独立一等对象仍在规划（`general_agent_framework_target_architecture.md` 5.3 节）
3. **测试覆盖率阈值偏低**：CI 里 `--cov-fail-under=30`，真正要达到企业级需要 60%+
4. **前端缺 TS 化**：Vue 侧还是 JS，前后端 API 契约没通过 pydantic → OpenAPI → 前端类型打通
5. **worktree 隔离只占位未接入**：`WorktreeRunRecord` 表已存在但实际 git worktree 操作尚未落地
6. **MCP 仍偏短连接**：长连接 session 复用、audit trail 还在完善

**这些不是"缺陷"，是"已识别的下一阶段计划"**——这是这个项目成熟度的另一个证据。

## 8. HR 常见问题的应答稿

### Q: 这个项目是你一个人做的吗？
> 是，我一个人从 0 到 1 设计和实现的。需要强调的是，项目有非常完整的设计文档链：总方案 → 目标架构 → 路线图 → 子域方案 → 验收清单，这说明我不是"先写代码再补文档"，而是"协议先行、文档先行、小步迭代"。

### Q: 用了多久？
> 从零开始，迭代了几个月。期间经历过多次架构收敛——比如把 child run 从 planner metadata 升级为一等对象、把 run trace 从 planner item 附属升级为 run 原生能力。这些收敛每次都留下了架构稿和验收清单。

### Q: 最难的部分是什么？
> 不是某一个功能点，而是"如何把已有能力统一成一套运行时内核"。项目刚起步时做了很多功能点（planner、scheduler、subagent、policy、trace、memory、skill），但每个点都有自己的事件、状态、元数据。后来我做了一次大收敛，把它们统一到 `AgentRun / AgentEvent / ChildRun / ArtifactRef` 四个一等对象上。这次收敛决定了项目能不能作为后续垂域智能体的可复用底座。

### Q: 为什么不直接用 LangChain / LangGraph / AutoGen？
> 我用了 LangChain 的 `bind_tools` 和 message 类型，但核心执行循环是自研的。原因是：市面上的框架在"工具调用流式聚合、错误分类与降级、状态机、事件协议、运行时能力合同"这些层面给的抽象不够。我参考了 Claude Code 的公开架构，自己实现了一套更贴合通用智能体运行时需求的底座。

### Q: 这个项目有商业价值吗？
> 它的价值不在于直接卖给客户，而在于**下一个业务智能体要坐上去的椅子**。当我下一个做垂域 Agent 项目（比如客服、代码助手、数据分析助手）时，不需要再重写调度、权限、治理、可观测性、工具/Skill/MCP 三层能力面——直接往这个底座上加工具、加 Skill、加 MCP capability 就行。这是它真正的 ROI。

### Q: 为什么花这么多精力做文档？
> 因为这是个基座项目，不是业务项目。基座项目最怕"代码能跑但没人接得起来"——一旦只有作者自己能读懂，它就不是基座，只是我的私有玩具。`docs/` 下的 20 多份设计稿保证了其他人（或未来的自己）能在几小时内理解设计决策，而不是从代码里反向推导。

### Q: 你在这个项目里学到了什么？
> 三件事。第一，**协议先行** 比功能堆叠重要得多——先定 `AgentRun / AgentEvent` 协议再写代码，返工成本低一个量级。第二，**治理要内建** 而不是补丁——权限、审批、trace、审计如果最后再加，永远加不干净。第三，**文档的价值不在于写给别人**，而是逼自己把决策讲清楚——讲不清楚的架构多半是错的。

## 9. 一段可以直接贴到简历的项目段落

> **MyPrivateAgent — 通用智能体运行时框架**（2025 – 至今，个人项目）
>
> 自研通用智能体框架基座，为后续垂域 Agent 提供可复用运行时底座。参考 Anthropic Claude Code 架构，从零实现 FastAPI + Vue 3 全栈方案，代码规模 42K+ 行（后端 21K / 前端 13K / 测试 8K）。
>
> 核心贡献：
>
> - 自研 AgentHarness 核心循环（1.8K 行），支持流式工具调用分块聚合、bind_tools / 豆包原生双模降级、指数退避重试、相似调用防抖
> - 设计并落地运行时一等对象协议：`AgentRun / AgentEvent / ChildRun / ArtifactRef`，显式状态机非法迁移抛错、任意执行可按 run_id 回放
> - 实现父子执行模型：planner item fan-out → multi child run，子智能体按角色注册（frontend/backend/qa/docs），工具白名单、provider 自动降级
> - 构建三层能力面（Tool / Skill / MCP）与运行时能力合同，实现能力缺口识别与补强建议聚合
> - 落地治理闭环：PolicyEngine 确定性前置判定、PermissionService 审批、AgentHook 生命周期钩子、RunTrace 统一追踪、Doctor 自检、QualityGate CI 门禁
> - 前端实现 10+ 治理面板（Runtime Debug / Planner / Governance Timeline / MCP / Capability Gap 等）与结构化卡片协议
> - 工程化：40+ 后端单测、10+ smoke 脚本、CI 四 Job 流水线（lint/tests/quality-gate/build）、Alembic 迁移、Vercel 一体化部署
> - 撰写 20+ 份架构设计稿，按"协议先行、文档先行、小步迭代"方法论演进项目

## 10. 需要你在简历上避免的地方

- **不要说"搭了一个 chatbot"**——这个项目的定位是框架基座，chatbot 只是它的 demo 入口。把它讲成 chatbot，面试官会低估它 90% 的价值。
- **不要过度吹"对齐 Claude Code"**——诚实版是"参考架构、选择性吸收边界设计"，不是复刻。过度吹反而会被追问到露馅。
- **不要回避未完成部分**——主动说出"类型化记忆未落地、权限模型单层、覆盖率阈值 30%"反而加分，因为它说明你对项目成熟度有清醒认知。
