# MyPrivateAgent Docs

> 当前主入口。MyPrivateAgent 的正式定位是企业级 Agent Runtime Control Plane：它负责 Runtime Core、ToolRuntime、Query Control、Governance Timeline、权限、审计、provider contract、framework adapter normalization 和业务系统集成边界。

## 当前应该先读什么

| 你的目标 | 从这里开始 | 当前完成线 |
|---|---|---|
| 理解项目是什么 | [Agent Runtime Control Plane Entrypoint](./architecture/agent_runtime_control_plane_entrypoint.md) | 项目不是单一 chat demo，也不是 LangGraph/CrewAI/Qwen-Agent/OpenAI Agents SDK 等外部框架的替代实现 |
| 看当前事实架构 | [当前架构总览](./architecture/current_architecture.md) | Runtime Core / Capability / Governance / Delivery 四层已收口为主解释框架 |
| 看运行层战略 | [运行层集成战略](./architecture/runtime_plane_integration_strategy.md) | 运行层用成熟框架和 adapter 接入，控制面只管治理与 contract |
| 查运行时 contract | [Runtime Contracts](./architecture/runtime_contracts.md) | Runtime Surface、Provider、Query Control、SDK、ToolRuntime 等 contract 以代码和 canonical spec 为真源 |
| 选择扩展路径 | [Extension Points](./architecture/extension_points.md) | 新能力先选 seam，再开 OpenSpec；不要直接改默认 chat 或绕过治理层 |
| 接入外接 Provider | [Capability Runtime Registry](./guides/capability_runtime_registry.md) | 走 provider onboarding catalog + service-provider management + UI surface + acceptance gate；accepted 只代表显式 managed-provider consumption |
| 开发垂域 Agent | [Domain Agent Development Guide](./guides/domain_agent_development_guide.md) | manifest 只读登记、capability linkage、trial/package/composition；不自动推广默认 `/api/chat` 检索注入 |
| 嵌入 SDK / Harness | [Project Entrypoint Checklist](./guides/project_entrypoint_checklist.md) | Embedded SDK 已有 preview + recovery/persistence 第一刀，完整 worker lease / durable continuation 仍 gated |
| 新增 Framework Adapter | [Extension Points: Framework Adapter](./architecture/extension_points.md#5-新增外部-framework-adapter) | adapter 先走 authoring checklist / precheck / pilot / promotion gate，不直接进默认 main chat |
| 看下一阶段优先级 | [Next Phase Hardening](./roadmap/next_phase_hardening.md) | Provider 接入链路已收口，默认回到控制面入口、Embedded SDK / Execution Loop 或 adapter checklist |

## 四条接入路径

### 1. 外接 Provider

适用于 `unifiedKnowledgeRAG`、语音、OCR、Layout、VLM 和后续独立能力服务。

当前入口：

- `GET /api/provider-onboarding`
- `GET /api/provider-onboarding/{onboarding_id}/readiness`
- `GET /api/service-providers`
- `python backend\scripts\provider_onboarding_acceptance_smoke.py --onboarding-id knowledge-rag-provider --pretty`

边界：

- `accepted` 只表示显式 managed-provider consumption ready。
- 不表示默认 `/api/chat` RAG、GraphRAG、source binding automation 或 final answer policy 已启用。
- 不把向量库、图数据库、OCR/VLM/ASR/TTS 引擎放进 MyPrivateAgent 主后端。

### 2. 垂域 Agent

适用于业务 agent 资产登记、试接和受治理问答路径。

当前入口：

- `backend/domain_agents/<agent_id>/agent.yaml`
- `GET /api/agents`
- `python backend\scripts\domain_agent_trial_smoke.py --payload docs\examples\domain_agent_trial_payload.json --pretty`

边界：

- manifest discovery 是只读登记，不自动注册 tool/skill/MCP/RAG。
- trial/package/composition 是显式控制面试接，不启用默认 chat retrieval injection。

### 3. Embedded SDK / Agent Harness

适用于把 MyPrivateAgent 作为库嵌入垂域 Python 项目。

当前入口：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `openspec/specs/agent-harness-facade-v1/spec.md`
- `openspec/specs/embedded-sdk-recovery-protocol/spec.md`

边界：

- SDK 已有 run/event/approval/tool continuation/recovery evidence 第一刀。
- 完整 durable continuation、worker ownership、跨进程 lease 和生产恢复仍需后续 gate。

### 4. Framework Adapter

适用于 LangGraph、CrewAI、Qwen-Agent、OpenAI Agents SDK、DeerFlow、Agno 等外部框架接入。

当前入口：

- `backend/agent_framework/framework_adapter_spi/`
- `backend/services/framework_adapter_runtime_service.py`
- `openspec/specs/framework-adapter-authoring-checklist/spec.md`

边界：

- 外部框架是 execution adapter candidate，不是项目定位。
- precheck / pilot ready 不等于默认 main chat execution ready。
- 任何 promotion 都必须另开 OpenSpec，并保留 local Runtime Core / Governance contracts 为真源。

## 默认工作节奏

```text
规格 -> 实现 -> 验证 -> 归档
```

需要先开 OpenSpec 的情况：

- runtime contract、read model、治理语义变化
- provider/API/adapter 行为变化
- 默认 chat 行为变化
- SDK / ToolRuntime / Approval / Recovery 边界变化

最小验证：

```powershell
openspec validate --all --strict
```

涉及代码时再加 focused backend/frontend test。不要为了文档入口产品化运行 `npm build`。

---

# Docs 索引

## 0. 对外介绍与简历话术（新增）
- [project_master_briefing.md](./superpowers/project_master_briefing.md)：主讲稿 + 学习导图整编版，适合首次快速建立项目认知、准备技术面试与压缩 HR 话术
- [project_overview.md](./superpowers/project_overview.md)：项目全景文档，覆盖分层架构、核心执行链、七大子系统、成熟度判断与已知债务
- [project_resume_pitch.md](./superpowers/project_resume_pitch.md)：简历与 HR 沟通话术，包含电梯版、30 秒版、亮点清单与常见追问应答
- [project_interview_qa.md](./superpowers/project_interview_qa.md)：面试深度问答，覆盖架构、并发、数据、治理、能力面、前端、CI 与工程决策
- [resume_bullet_points.md](./superpowers/resume_bullet_points.md)：可直接复用的技术简历段落，包含标准、精简、后端架构、全栈与工程化五个版本

## 1. 先看这几份
- [../.specify/memory/constitution.md](../.specify/memory/constitution.md)：Spec Kit 项目宪章，约束 AI 协作开发、runtime contract 收口、文档同步和外部参考使用边界
- [../openspec/config.yaml](../openspec/config.yaml)：OpenSpec 默认上下文与规格规则，约束 proposal / tasks / archive 输出如何贴合本项目
- [../openspec/README.md](../openspec/README.md)：OpenSpec 在本仓库中的实际使用说明，包含何时开 change、目录结构、样板和与 Spec Kit 的分工
- [architecture/project_core_overview.md](./architecture/project_core_overview.md)：项目核心总览，面向维护者、垂域智能体开发者和外部前端接入方，说明核心分层、主执行链和当前统一 API
- [guides/domain_agent_development_guide.md](./guides/domain_agent_development_guide.md)：垂域智能体开发指南，说明 agent 目录、`agent.yaml` 只读登记、Prompt/Tool/Skill/MCP/RAG/Policy 放置方式和前端统一对接协议
- [guides/external_rag_provider_development.md](./guides/external_rag_provider_development.md)：外部 Knowledge Provider / RAG 项目开发规范，说明 RAG、知识图谱、引用证据、健康检查和 MyPrivateAgent 接入环境变量
- [guides/external_rag_graphrag_provider_design.md](./guides/external_rag_graphrag_provider_design.md)：独立 RAG / GraphRAG Provider 设计指南，说明 LlamaIndex 文档 RAG、Neo4j GraphRAG、source catalog、API 合同和规格到归档节奏
- [guides/capability_runtime_registry.md](./guides/capability_runtime_registry.md)：统一能力运行时注册中心指南，说明 OCR、ASR、TTS、多模态、视频生成等能力如何统一注册、调用和服务化迁移
- [guides/voice_runtime_module.md](./guides/voice_runtime_module.md)：Legacy local voice runtime fallback 说明，标记 `backend/voice_runtime/` 和 `/api/voice/*` 仅为兼容层，推荐语音路径是外部 `unifiedTTSandASR`
- [../openspec/specs/query-workspace-generalization/spec.md](../openspec/specs/query-workspace-generalization/spec.md)：Query Workspace 通用化主规格，定义哪些 query 能力可以从 `main_chat` 提升为通用模式
- [../openspec/specs/channel-promotion-gate/spec.md](../openspec/specs/channel-promotion-gate/spec.md)：Channel Promotion Gate 主规格，定义 channel 从 readiness 到 recent summary / detail / history / workspace 的逐层推广门槛
- [architecture/current_architecture.md](./architecture/current_architecture.md)：当前架构事实入口，说明 Runtime Core、Capability、Governance、Delivery 四层结构和当前已收口能力
- [architecture/runtime_contracts.md](./architecture/runtime_contracts.md)：运行时契约索引，说明 Runtime Surface 当前暴露的 contract、来源文件和维护约束
- [architecture/recent_summary_abstraction_note.md](./architecture/recent_summary_abstraction_note.md)：Recent Summary 抽象判断，说明为什么当前先固定共享字段集合，不立即抽通用 assembler
- [architecture/reference_project_mapping.md](./architecture/reference_project_mapping.md)：外部参考项目映射，说明 `learn-claude-code / self-improving-agent / claude-code` 借什么、不借什么、落到我方哪里
- [architecture/extension_points.md](./architecture/extension_points.md)：扩展点索引，说明垂域智能体、工具、MCP、Skill/Memory、外部框架 Adapter 和治理策略应从哪里接入
- [roadmap/next_phase_hardening.md](./roadmap/next_phase_hardening.md)：下一阶段硬化路线，记录 Phase G 后 Agent Runtime 主干、Self-Improvement Ledger、Query Control Plane 的推荐顺序
- [demo_runbook.md](./demo_runbook.md)：Demo 启动、演示与排障手册
- [test_manual.md](./test_manual.md)：统一测试手册与测试案例，已收录 Phase D `pilot / precheck / external pilot / remediation` 专项验收顺序
- [agent_framework_starter_guide.md](./agent_framework_starter_guide.md)：新垂域 Agent 起步指南
- [agent_framework_demo_guide.md](./agent_framework_demo_guide.md)：当前 Demo 的框架边界与复用方式

## 2. 架构与路线
- [../.specify/memory/constitution.md](../.specify/memory/constitution.md)：项目级开发宪章，说明哪些改动必须先补 spec、哪些原则不可破
- [../openspec/config.yaml](../openspec/config.yaml)：OpenSpec 规格上下文与默认规则，适合作为功能/变更规格的入口配置
- [../openspec/README.md](../openspec/README.md)：OpenSpec 使用说明与当前仓库的规格工作流入口
- [architecture/project_core_overview.md](./architecture/project_core_overview.md)：项目核心总览与当前对外 API 入口
- [guides/domain_agent_development_guide.md](./guides/domain_agent_development_guide.md)：基于本框架开发垂域智能体的标准操作指南
- [guides/external_rag_provider_development.md](./guides/external_rag_provider_development.md)：外部 Knowledge Provider / RAG 项目标准接入指南
- [guides/external_rag_graphrag_provider_design.md](./guides/external_rag_graphrag_provider_design.md)：独立知识服务数据面设计指南，推荐 LlamaIndex 与 Neo4j GraphRAG 的适用边界
- [guides/capability_runtime_registry.md](./guides/capability_runtime_registry.md)：统一 AI 能力注册、health、invoke 与后续独立服务化规则
- [guides/voice_runtime_module.md](./guides/voice_runtime_module.md)：旧本地语音 fallback 与 `/api/voice/*` 兼容说明
- [../openspec/specs/query-workspace-generalization/spec.md](../openspec/specs/query-workspace-generalization/spec.md)：高层 query workspace 通用化真源，适合判断是否应继续扩 channel
- [../openspec/specs/channel-promotion-gate/spec.md](../openspec/specs/channel-promotion-gate/spec.md)：channel 推广 gate 真源，适合判断某个 channel 当前最多能推进到哪一层
- [architecture/current_architecture.md](./architecture/current_architecture.md)：当前通用智能体底座架构事实，推荐作为维护者和垂域接入方的第一入口
- [architecture/runtime_contracts.md](./architecture/runtime_contracts.md)：当前 Runtime Surface 与运行时契约事实
- [architecture/recent_summary_abstraction_note.md](./architecture/recent_summary_abstraction_note.md)：当前 recent summary 通用抽象的判断说明
- [architecture/reference_project_mapping.md](./architecture/reference_project_mapping.md)：当前外部参考项目与我方 runtime/governance/adapter 的映射真源
- [architecture/extension_points.md](./architecture/extension_points.md)：当前扩展 seam 与接入约束
- [roadmap/next_phase_hardening.md](./roadmap/next_phase_hardening.md)：Phase E 后续硬化优先级
- [change/2026-05-11-enterprise-agent-runtime-blueprint.md](./change/2026-05-11-enterprise-agent-runtime-blueprint.md)：企业内部通用智能体底座三阶段落地蓝图，明确推荐路线、三阶段实施边界、保留/重构/引入清单，并记录 Phase A 第一轮落地状态
- [change/2026-05-11-phase-a-runtime-core-implementation-plan.md](./change/2026-05-11-phase-a-runtime-core-implementation-plan.md)：Phase A 统一运行时内核实施计划，按任务拆分 runtime、approval、scheduler、trace 与前端最小对齐，并记录本轮回归验证结果
- [change/2026-05-11-phase-b-capability-layer-design-and-plan.md](./change/2026-05-11-phase-b-capability-layer-design-and-plan.md)：Phase B 能力层与 Adapter 体系设计方案，拆分 Tool Runtime、ArtifactRef、MCP Runtime、Skill/Memory、Command/SDK 与外部框架 Adapter 的阶段计划
- [change/2026-05-11-phase-c-runtime-contract-hardening-plan.md](./change/2026-05-11-phase-c-runtime-contract-hardening-plan.md)：Phase C 运行时契约硬化方案，记录 Contract Snapshot Guard、adapter pilot 全链路和质量门禁规划
- [change/2026-05-12-phase-d-framework-adapter-readiness-and-governance-plan.md](./change/2026-05-12-phase-d-framework-adapter-readiness-and-governance-plan.md)：Phase D 外部 Framework Adapter readiness 与治理收口文档，记录 LangGraph draft adapter、precheck、external pilot、doctor remediation、Runtime Surface 与 Governance Timeline 当前完成面
- [change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md](./change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md)：Phase D-8 / D-9 真实外部 Framework Adapter 最小执行骨架设计稿，定义 LangGraph runtime client、translator、external pilot 与错误分类边界，并记录当前已完成到 Slice 6 的实现状态
- [change/2026-05-13-phase-e-architecture-hardening-plan.md](./change/2026-05-13-phase-e-architecture-hardening-plan.md)：Phase E 架构硬化与产品化整理计划，记录 diagnostics seam 抽取、后续 adapter SPI / runtime service / 前端治理台瘦身顺序
- [change/2026-05-16-phase-g-agent-runtime-reference-alignment.md](./change/2026-05-16-phase-g-agent-runtime-reference-alignment.md)：Phase G 外部参考项目对齐与 Agent Runtime 主干硬化方案，记录 Claude Code 相关项目可借鉴设计和 Self-Improvement Ledger contract 第一刀
- [general_agent_framework_enterprise_plan.md](./general_agent_framework_enterprise_plan.md)：基于当前仓库现状的企业级完善总方案
- [general_agent_framework_target_architecture.md](./general_agent_framework_target_architecture.md)：目标运行时架构、模块边界与数据结构设计稿
- [claude_alignment_improvement_plan.md](./claude_alignment_improvement_plan.md)：对齐 Claude Code 的下一阶段完善方案
- [agent_framework_enterprise_roadmap.md](./agent_framework_enterprise_roadmap.md)：从 Demo 演进到成熟通用智能体框架的路线图
- [demo_storage_architecture_plan.md](./demo_storage_architecture_plan.md)：Demo 默认采用本地优先策略的存储架构方案
- [planner_todo_framework_plan.md](./planner_todo_framework_plan.md)：Planner/Todo 建设计划
- [mcp_registry_framework_plan.md](./mcp_registry_framework_plan.md)：MCP 注册中心与能力目录建设计划
- [skill_runtime_framework_plan.md](./skill_runtime_framework_plan.md)：Skill Runtime 运行时集成计划
- [feedback_learning_governance_plan.md](./feedback_learning_governance_plan.md)：反馈与学习治理进度和下一步规划

## 3. 协议与专项
- [agent_framework_card_schemas.md](./agent_framework_card_schemas.md)：结构化卡片协议
- [test_manual.md](./test_manual.md)：当前统一测试基线与测试案例
