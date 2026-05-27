# Design

## Registry Boundary

`DomainAgentRegistryService` 是只读资产 registry。它扫描 `backend/domain_agents/*/agent.yaml` 或 `agent.yml`，解析稳定字段并返回 Runtime Surface contract。

它不导入垂域 agent 的 Python 代码，不执行工具，不建立 MCP session，也不修改 skill registry。这样可以先把企业级资产盘点、治理可见性和目录约定落地，同时避免提前把执行路径复杂化。

## Manifest Contract

最小 manifest 要求：

- `id`
- `name`
- `version`
- 至少一个 `roles[].id`

可选字段：

- `description`
- `runtime`
- `capabilities.tools`
- `capabilities.skills`
- `capabilities.mcp_servers`
- `capabilities.rag_sources`
- `governance.approval_required`
- `governance.audit_tags`

Registry 只做结构归一化和错误汇总。manifest 缺失必填字段时，该 agent 进入 `invalid`，不会影响其他 agent 被读取。

## Runtime Surface Shape

`domain_agent_registry` 返回：

- `contract_version`
- `status`: `empty | ready | degraded`
- `root_path`
- `total_agents`
- `ready_agents`
- `invalid_agents`
- `agents`
- `errors`

该 contract 用于前端治理面、垂域 agent 列表和后续 agent catalog 工作的真源。

## Future Work

后续可单独开 change 增加：

- agent enable/disable 与权限编辑。
- `/api/agents` catalog API。
- `/api/agents/{agent_id}/chat` 包装入口。
- manifest 驱动的 tool / skill / MCP / RAG 自动注册。
- framework adapter 选择策略。
