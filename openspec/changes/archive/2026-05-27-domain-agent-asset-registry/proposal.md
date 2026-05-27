# Domain Agent Asset Registry

## Why

`backend/domain_agents/<agent_id>/` 已经被文档定义为垂域智能体的推荐组织方式，但当前运行时还没有统一的只读登记入口。这样会导致垂域 agent 资产、角色、能力和治理边界只能停留在文档约定，无法被 Runtime Surface、治理台或后续前端项目稳定读取。

## What Changes

- `backend/domain_agents/<agent_id>/agent.yaml` 作为垂域智能体资产声明。
- `DomainAgentRegistryService` 作为只读 registry，不参与执行路由。
- Runtime Surface 暴露 `domain_agent_registry`，供前端和治理面查看当前垂域 agent 资产。
- 垂域开发文档同步到“目录约定已具备只读登记能力”的项目状态。

## Non-goals

- 不新增 `/api/agents/{agent_id}/chat`。
- 不改变 `POST /api/chat` 的主执行路径。
- 不实现 agent enable/disable、热加载、数据库持久化或权限编辑后台。
- 不接入 LangGraph/OpenAI Agents SDK/Qwen-Agent/DeerFlow 等外部框架 adapter。
- 不自动注册工具、MCP server、RAG source 或 skill，仅登记 manifest 中声明的资产。

## Impact

- Backend contract: `RuntimeSurfaceService` profile 新增 `domain_agent_registry`。
- Runtime service: 新增 `backend/services/domain_agent_registry_service.py`。
- Documentation: 更新垂域智能体开发指南和扩展点说明。
- Tests: 新增 focused unittest 覆盖 manifest 扫描、缺失字段、空目录和 Runtime Surface 暴露。
