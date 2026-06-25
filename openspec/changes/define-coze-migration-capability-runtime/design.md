## Context

MyPrivateAgent 当前定位是企业级 Agent Runtime Control Plane。现有框架已经具备 domain agent manifest、unified capability runtime、ToolRuntime、MCP Runtime、Skill Runtime、Runtime Surface 和 Governance Timeline 的基础合同。Coze 迁移不应新增一条孤立执行链，而应把原 Coze 工作流沉淀为可登记、可治理、可统一调用的运行时能力。

团队迁移的主要协作风险不是单个流程跑不通，而是多人把 Coze 节点、Prompt、插件依赖和调用入口分别迁到不同位置，导致后续无法统一追踪、审计、复用、权限控制和回归验证。

## Goals / Non-Goals

**Goals:**

- 给 Coze 迁移工作流定义唯一推荐资产目录：`backend/coze_workflows/<workflow_id>/`。
- 用 `workflow.yaml` 固定工作流身份、版本、owner、输入输出 schema、Prompt 资产、依赖能力、权限、验收样例和治理边界。
- 让迁移工作流通过统一 registry 暴露为 capability-like runtime asset。
- 让调用方只能通过统一入口触发工作流，并在执行时获得 `run_id`、状态、结构化结果、错误和 trace 关联。
- 让 domain agent 可以声明关联 Coze 工作流能力，但不能绕过 registry 自动执行。
- 为后续多人协作、review、CI smoke、文档和治理台展示留下稳定合同。

**Non-Goals:**

- 不批量迁移现有 Coze 流程。
- 不在第一阶段引入数据库迁移或复杂持久层。
- 不把 Coze 迁移能力直接塞进默认 `/api/chat`。
- 不把 LangGraph、CrewAI、OpenAI Agents SDK 或 Dify 作为默认执行引擎。
- 不在第一阶段建设完整低代码编辑器或可视化编排器。

## Decisions

### Decision 1: Coze 工作流资产统一放在 `backend/coze_workflows/<workflow_id>/`

推荐结构：

```text
backend/coze_workflows/
  customer_intake/
    workflow.yaml
    prompts/
      system.md
      task.md
    examples/
      happy_path.json
      plugin_unavailable.json
    README.md
```

`workflow_id` 使用 kebab-case 或 snake_case 的稳定机器名。一个目录只归属一个迁移工作流，目录内文件由该工作流 owner 维护。

替代方案：直接放在 `backend/domain_agents/<agent_id>/` 下。  
不选原因：domain agent 是垂域 agent 身份目录，Coze 工作流是可被多个 agent 复用的能力资产。混放会让 agent 身份、工作流能力和执行实现边界变乱。

### Decision 2: `workflow.yaml` 是迁移能力的唯一登记入口

`workflow.yaml` 必须包含：

- `id`
- `name`
- `version`
- `owner`
- `source.coze`
- `entrypoint`
- `inputs.schema`
- `outputs.schema`
- `prompts`
- `dependencies.tools`
- `dependencies.mcp_capabilities`
- `dependencies.skills`
- `dependencies.knowledge_sources`
- `governance.permission_level`
- `governance.trace_required`
- `acceptance.examples`
- `status`

Prompt 正文不直接写入 YAML，YAML 只引用 prompt 文件，避免 manifest 膨胀并便于 review。

替代方案：用 Python 装饰器注册。  
不选原因：装饰器适合代码插件，不适合从 Coze 迁移来的 Prompt、节点依赖、验收样例和治理元数据；也不利于非代码 owner review。

### Decision 3: Registry 只做发现和合同归一化，第一阶段 side-effect-free

Coze workflow registry 第一阶段只扫描 manifest、校验字段、归一化 contract、暴露 readiness 和错误，不执行工作流、不调用工具、不写入 trace。

替代方案：扫描到 manifest 后自动注册工具并进入 chat。  
不选原因：迁移初期会存在半成品流程，自动进入 chat 会扩大风险。必须先有 readiness、owner 和 acceptance 状态，再进入执行 promotion。

### Decision 4: 统一调用入口先映射到 capability runtime envelope

调用语义固定为：

```text
workflow_id + input payload -> run_id + status + result/error + trace refs
```

第一阶段可以提供专用入口，也可以映射为 `coze.workflow.<workflow_id>` capability，但返回 envelope 必须与 unified capability runtime 对齐。

替代方案：每个工作流自定义 FastAPI router。  
不选原因：多人迁移会产生大量自定义入口，权限、trace、错误和验收很难统一。

### Decision 5: Domain agent 只能声明关联，不拥有 Coze 工作流执行语义

`backend/domain_agents/<agent_id>/agent.yaml` 可以声明某个 agent 允许使用哪些 Coze 迁移工作流 capability，但执行授权仍由 Coze workflow registry、capability runtime、policy 和 run trace 决定。

替代方案：domain agent manifest 直接内嵌 Coze 工作流定义。  
不选原因：会把可复用 workflow 绑定到单个 agent，降低复用性并增加多人协作冲突。

### Decision 6: 外部框架只作为 workflow executor adapter 候选

如果某个 Coze 流程需要 LangGraph 或 OpenAI Agents SDK 等执行引擎，manifest 只能声明 `entrypoint.adapter = langgraph|openai_agents|local` 之类的候选执行器。adapter 仍必须输出本地 `run_id/event/result/error` 合同。

替代方案：把 LangGraph graph 文件作为本地真源。  
不选原因：本项目真源是 Runtime Core 和 Governance contract，外部 graph 只能作为执行实现，不应反向定义控制面合同。

## Risks / Trade-offs

- [Risk] Manifest 字段过多，迁移人员填写成本高。  
  Mitigation: 第一阶段只要求最小必填字段，复杂依赖可逐步补充；提供样例模板和 smoke 校验。

- [Risk] 只做 registry 不执行，短期看起来进展慢。  
  Mitigation: 这是多人协作的地基，先保证资产可发现、可校验、可治理，再逐个接入执行器。

- [Risk] Coze 原流程节点与自研能力无法一一对应。  
  Mitigation: manifest 允许声明 `migration_notes` 和 `unsupported_nodes`，并通过 readiness blockers 暴露缺口。

- [Risk] 团队成员绕过统一入口直接调用实现文件。  
  Mitigation: 规范明确禁止跨 workflow 目录 import，后续通过 lint/smoke 或 code review gate 固化。

## Migration Plan

1. 先落地 OpenSpec 合同和文档真源。
2. 新增 Coze workflow authoring guide 和 manifest 模板。
3. 实现 side-effect-free registry，扫描 `backend/coze_workflows/*/workflow.yaml`。
4. 将 registry contract 暴露到 Runtime Surface 或 dedicated read endpoint。
5. 选择 1 个简单 Coze 流程做样板目录和 smoke。
6. 再接入统一 invoke 入口和最小执行器。
7. 最后评估是否需要 LangGraph/OpenAI Agents SDK adapter。

Rollback 策略：第一阶段只有新增目录、registry 和只读 contract；若发现规范不合适，可删除 registry 暴露并保留样例目录，不影响现有 chat/runtime 主链路。

## Open Questions

- 第一批样板工作流选哪个真实 Coze 流程更能覆盖 Prompt、工具依赖和异常路径？
- 统一调用入口先做 dedicated `/api/coze-workflows/{workflow_id}/invoke`，还是直接注册为 `/api/capabilities/coze.workflow.<id>/invoke`？
- `workflow_id` 是否统一用 kebab-case，还是为了兼容 Python import 允许 snake_case？
