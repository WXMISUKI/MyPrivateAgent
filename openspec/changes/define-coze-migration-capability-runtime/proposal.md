## Why

公司现有大量智能体和工作流沉淀在 Coze 低代码平台中，迁移到自研 Agent Runtime 时，如果缺少统一目录、统一 manifest、统一注册和统一调用入口，多人并行迁移会快速产生入口分散、Prompt 分散、工具依赖不透明、权限不可控、追踪不可回放等协作风险。

本变更先把 Coze 迁移规范固化为 MyPrivateAgent 的正式运行时能力契约，让每个迁移工作流都能像能力资产一样被登记、治理、调用和验收，而不是由各团队成员各自散落实现。

## What Changes

- 明确 Coze 迁移工作流的标准资产目录、必备文件和命名规则。
- 定义 `coze workflow manifest`，用于描述原 Coze 工作流身份、入口参数、输出 schema、Prompt 资产、工具/MCP/Skill/知识源依赖、权限等级、owner 和验收样例。
- 定义迁移能力注册边界：迁移工作流必须进入统一 registry 后，才能被主入口、专属入口或后续调度器调用。
- 定义统一调用入口：调用方使用稳定 `workflow_id / capability_id / run_id` 合同触发迁移能力，不直接 import 具体工作流实现文件。
- 定义多人协作边界：每个迁移工作流有独立目录、owner、版本、验收样例和禁止跨目录隐式依赖规则。
- 定义治理要求：迁移能力必须暴露权限、工具依赖、外部 provider 依赖、运行 trace、失败分类和验收状态。
- 定义与现有 domain agent registry、unified capability runtime、runtime contract gate 的关系，避免为 Coze 迁移新增旁路控制面。

### 收口对象

- Coze 工作流迁移后的资产布局。
- Coze 工作流到 MyPrivateAgent 能力注册表的 manifest 契约。
- Coze 迁移能力被统一调用、追踪、审计和验收的最小运行时边界。
- 多人并行迁移时的 owner、目录、版本、依赖和验收协作规范。

### 非目标

- 不在本阶段批量迁移所有 Coze 工作流。
- 不在本阶段引入完整多租户、组织级 RBAC 或复杂审批后台。
- 不在本阶段把 LangGraph、CrewAI、OpenAI Agents SDK、Dify 等外部框架作为默认执行引擎。
- 不在本阶段重写 Runtime Core、ToolRuntime、MCP Runtime 或 Domain Agent Registry。
- 不在本阶段直接做数据库迁移；第一阶段优先使用 side-effect-free registry / contract / smoke 方式验证。

## Capabilities

### New Capabilities

- `coze-migration-capability-runtime`: 定义 Coze 工作流迁移资产、manifest、registry、统一调用入口、治理追踪和验收样例的运行时契约。

### Modified Capabilities

- `domain-agent-asset-registry`: 增加 Coze 迁移工作流资产与 domain agent manifest 的关联规则，明确迁移工作流可以作为 domain agent 的 capability 资产被发现，但不能绕过正式 registry 自动执行。
- `unified-capability-runtime`: 增加 Coze 迁移能力作为 provider-neutral capability 的暴露和调用要求，明确调用入口必须返回统一 envelope、健康状态和结构化错误。

## Impact

- 后端 contract：
  - `backend/domain_agents/<agent_id>/agent.yaml` 的能力关联语义。
  - 未来新增 `backend/coze_workflows/<workflow_id>/workflow.yaml` 或等效 registry root。
  - Runtime Surface 中的 domain agent registry、capability contract、runtime contract gate。
  - 后续统一执行入口，例如 `POST /api/coze-workflows/{workflow_id}/invoke` 或映射到通用 capability invoke。
- 前端消费点：
  - Settings / Runtime Surface / Governance Timeline 后续可展示 Coze 迁移能力 readiness、owner、依赖、验收状态和最近运行结果。
  - 不要求本阶段新增复杂 UI，只要求 contract 可被前端稳定消费。
- 文档真源：
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - 后续可新增 Coze 迁移开发指南，例如 `docs/guides/coze_migration_workflow_authoring.md`
- 外部借鉴边界：
  - 借鉴 LangGraph / OpenAI Agents SDK / CrewAI 的 run、tool、handoff、trace、flow/team 分层思想。
  - 不照搬任何外部框架的目录结构、执行模型或前端治理台 payload。
  - 所有外部执行引擎只允许作为后续 adapter candidate，必须映射回本地 Runtime Core / Capability / Governance 合同。
