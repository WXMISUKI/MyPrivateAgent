# MCP Registry Framework Plan

## Goal
Add a Claude Code style minimal MCP registry layer so the agent framework can manage external capability servers through a stable configuration and API boundary.

## Delivered In This Phase

- `backend/services/mcp_registry_service.py`
  - persistent JSON-backed MCP server registry
  - stdio/http transport validation
  - enable/disable governance
  - capability catalog aggregation
  - capability-based server resolution
- `backend/routers/mcp.py`
  - `GET /api/mcp/servers`
  - `POST /api/mcp/servers`
  - `PATCH /api/mcp/servers/{server_name}`
  - `DELETE /api/mcp/servers/{server_name}`
  - `POST /api/mcp/servers/{server_name}/enable`
  - `POST /api/mcp/servers/{server_name}/disable`
  - `GET /api/mcp/catalog`
- `backend/schemas.py`
  - MCP server create/update/response schemas
  - capability catalog schemas
- `backend/agent_server/router_registry.py`
  - MCP router group registration
- `backend/data/mcp_servers.json`
  - default persisted registry file
- `backend/services/mcp_runtime_service.py`
  - converts enabled MCP capabilities into runtime tools
  - syncs capability tools into the harness registry before execution
  - resolves primary provider for a capability at invocation time
  - keeps stale capability tools removed when registry changes
- `backend/services/mcp_adapter_service.py`
  - adds minimal per-server probe / handshake semantics
  - stdio servers are validated through local command discovery
  - http servers are validated through URL parsing
  - runtime capability execution now performs minimal real dispatch
    - stdio: subprocess JSON payload request
    - http: JSON POST request
- `backend/services/mcp_session_service.py`
  - adds a first session-level handshake skeleton
  - sends `initialize` and `tools/list` JSON-RPC requests
  - normalizes server info, protocol version, capabilities, tools, and audit records
  - caches handshake results per server
  - supports protocol-level `tools/call`
  - resolves capability -> tool mapping through server metadata and handshake result
- `backend/routers/mcp.py`
  - adds `POST /api/mcp/servers/{server_name}/handshake`
  - adds `POST /api/mcp/servers/{server_name}/tools/{tool_name}/call`
- `frontend-vue/src/stores/mcp.js`
  - wraps MCP server CRUD, catalog refresh, probe, handshake, and tool call actions
- `frontend-vue/src/components/McpManagementPanel.vue`
  - adds a reusable MCP management panel inside settings
  - supports server form submission, enable/disable, probe, handshake, and tools/call diagnostics
- `frontend-vue/src/views/SettingsView.vue`
  - integrates MCP management into the main settings surface
- planner/runtime capability guard
  - planner `required_capabilities` are now checked before specialized execution starts
  - missing or unavailable capabilities will block the active plan item
  - orchestrator also performs a defensive capability guard for direct runtime safety

## Why This Matters

- It creates a real configuration boundary for external tool ecosystems.
- It gives planner, skills, and future subagents a stable way to discover external capability providers.
- It avoids hardcoding MCP server details directly inside orchestrator or tool code.
- It establishes a runtime bridge between MCP registry data and the existing harness tool system.
- It closes the gap between planner intent and execution reality: a step that declares required MCP capabilities can now be stopped deterministically before the agent hallucinates around missing infrastructure.

## Current Limitations

- This phase now performs minimal config-level probe, minimal real transport dispatch, `initialize/tools/list`, cached session reuse, and protocol-level `tools/call`, but still does not implement the full MCP lifecycle.
- There is no connection pool, heartbeat, or runtime health probe.
- Capability tools can now try session-level `tools/call`, but the runtime is still not a fully stateful long-lived MCP session manager.
- The frontend now has a minimal MCP management panel, but it still lacks richer edit flows, history, and operator-grade observability.
- Planner capability guard is now enforced for the active chat/planner path, but there is still no generalized scheduler-level policy engine.

## Recommended Next Steps

1. Add long-lived session lifecycle management, notification handling, and explicit invalidation/reconnect policy.
2. Add stronger tool schema normalization and capability-to-tool governance validation.
3. Add connection pool, health state cache, and retry/backoff policy.
4. Promote capability guard from chat path to a generalized scheduler/orchestrator policy layer.
5. Expand the frontend MCP panel with history, health indicators, and server metadata helpers.
