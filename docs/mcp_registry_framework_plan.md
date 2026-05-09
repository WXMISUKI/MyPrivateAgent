# MCP Registry 框架建设计划

## 目标

增加一层 Claude Code 风格的最小 MCP registry，使智能体框架能够通过稳定的配置和 API 边界管理外部能力服务器。

## 本阶段已交付

- `backend/services/mcp_registry_service.py`
  - 持久化的 JSON-backed MCP server registry
  - stdio / http transport 校验
  - enable / disable 治理
  - capability catalog 聚合
  - 基于 capability 的 server resolution
- `backend/routers/mcp.py`
  - `GET /api/mcp/servers`
  - `POST /api/mcp/servers`
  - `PATCH /api/mcp/servers/{server_name}`
  - `DELETE /api/mcp/servers/{server_name}`
  - `POST /api/mcp/servers/{server_name}/enable`
  - `POST /api/mcp/servers/{server_name}/disable`
  - `GET /api/mcp/catalog`
- `backend/schemas.py`
  - MCP server create / update / response schemas
  - capability catalog schemas
- `backend/agent_server/router_registry.py`
  - MCP router group 注册
- `backend/data/mcp_servers.json`
  - 默认持久化 registry 文件
- `backend/services/mcp_runtime_service.py`
  - 将启用的 MCP capabilities 转成运行时工具
  - 在执行前将 capability tools 同步到 harness registry
  - 在调用时解析某个 capability 的 primary provider
  - 当 registry 变化时移除陈旧 capability tools
- `backend/services/mcp_adapter_service.py`
  - 增加最小 per-server probe / handshake 语义
  - stdio server 通过本地命令发现做校验
  - http server 通过 URL 解析做校验
  - 运行时 capability execution 现在会执行最小真实分发
    - stdio：子进程 JSON payload 请求
    - http：JSON POST 请求
- `backend/services/mcp_session_service.py`
  - 增加第一版 session-level handshake skeleton
  - 发送 `initialize` 和 `tools/list` JSON-RPC 请求
  - 归一化 server info、protocol version、capabilities、tools 和 audit records
  - 按 server 缓存 handshake 结果
  - 支持协议级 `tools/call`
  - 通过 server metadata 和 handshake 结果解析 capability -> tool 映射
- `backend/routers/mcp.py`
  - 新增 `POST /api/mcp/servers/{server_name}/handshake`
  - 新增 `POST /api/mcp/servers/{server_name}/tools/{tool_name}/call`
- `frontend-vue/src/stores/mcp.js`
  - 封装 MCP server CRUD、catalog refresh、probe、handshake 和 tool call actions
- `frontend-vue/src/components/McpManagementPanel.vue`
  - 在 settings 内新增可复用的 MCP 管理面板
  - 支持 server 表单提交、enable / disable、probe、handshake 和 tools/call 诊断
- `frontend-vue/src/views/SettingsView.vue`
  - 将 MCP 管理能力集成到主 settings 界面
- planner / runtime capability guard
  - planner 的 `required_capabilities` 现在会在专业化执行开始前校验
  - 缺失或不可用能力会阻断 active plan item
  - orchestrator 也会执行防御式 capability guard，保证直接运行时安全

## 为什么这很重要

- 它为外部工具生态建立了真实的配置边界。
- 它让 planner、skills 和未来 subagents 拥有稳定的外部 capability provider 发现方式。
- 它避免把 MCP server 细节直接硬编码进 orchestrator 或工具代码。
- 它建立了 MCP registry 数据与现有 harness tool system 之间的运行时桥接。
- 它补上了 planner 意图与执行现实之间的断层：声明了 `required_capabilities` 的步骤，现在可以在基础设施缺失时被确定性阻断，而不是让 agent 围绕缺失能力产生幻觉式补偿。

## 当前限制

- 本阶段已经具备最小配置级 probe、最小真实 transport dispatch、`initialize/tools/list`、缓存 session reuse 和协议级 `tools/call`，但仍未实现完整的 MCP 生命周期。
- 目前没有 connection pool、heartbeat 或运行时 health probe。
- capability tools 现在可以尝试 session-level `tools/call`，但运行时仍然不是完整的有状态长生命周期 MCP session manager。
- 前端已有最小 MCP 管理面板，但仍缺少更丰富的编辑流程、历史记录和运营级可观测性。
- planner capability guard 目前只覆盖 active chat / planner path，还没有泛化为 scheduler 级 policy engine。

## 推荐下一步

1. 增加长生命周期 session 生命周期管理、通知处理，以及明确的 invalidation / reconnect 策略。
2. 增加强化的 tool schema 归一化和 capability-to-tool 治理校验。
3. 增加 connection pool、health state cache 和 retry / backoff 策略。
4. 将 capability guard 从 chat path 提升为通用 scheduler / orchestrator policy layer。
5. 扩展前端 MCP 面板，补充历史、健康指示和 server metadata 辅助信息。
