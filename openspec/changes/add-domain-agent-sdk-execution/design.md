# Design: Domain Agent SDK Execution Integration

## Context

The domain agent catalog (`/api/agents`) is read-only and manifest-driven. The chat endpoint uses `SimplifiedOrchestrator`. The SDK path is proven end-to-end but disconnected from the system. No API endpoint executes domain agents through the SDK path.

## Goals

1. Register a reference domain agent (weather assistant) in the catalog.
2. Create a service that maps agent manifests to `AgentHarnessFacade` instances.
3. Add an API endpoint that executes domain agents through the SDK path.
4. Return governance trace as part of the response.

## Non-Goals

1. No changes to `/api/chat`.
2. No persistence/recovery.
3. No streaming.
4. No child executor.
5. No frontend changes.

## Key Decisions

### Decision 1: New endpoint, not modify existing chat

Create `POST /api/agents/{agent_id}/execute` instead of modifying `/api/chat`. This:
- Zero risk to existing functionality
- Clean separation of concerns
- Easy to iterate independently

### Decision 2: DomainAgentExecutionService as the bridge

Create a service that:
- Reads the agent manifest (`agent.yaml`)
- Resolves tools from the manifest's `capabilities.tools` list
- Creates an `AgentHarnessFacade` with registered tools
- Executes via `facade.execute(model_name=...)`

This service is the bridge between the manifest-driven catalog and the SDK execution path.

### Decision 3: Tool resolution from manifest

The agent manifest declares tools (e.g., `query_weather`). The execution service resolves these to actual handlers. For the weather agent, handlers are in `backend/domain_agents/weather_assistant/tools.py`.

For future agents, tool resolution can be extended to:
- MCP servers (via `mcp_servers` in manifest)
- Skills (via `skills` in manifest)
- External tool registries

### Decision 4: Synchronous response with governance trace

The endpoint returns a synchronous JSON response with:
- `output`: the model's final response text
- `events`: the governance trace events
- `run`: the run snapshot (state, metadata, state_history)

This matches the SDK's synchronous execution model and provides full governance visibility.

## Risks

| Risk | Mitigation |
|------|-----------|
| Tool resolution is simple (direct handler mapping) | Document that MCP/skill resolution is future work |
| No streaming | Document that streaming is future work |
| Single-domain only (weather) | Pattern is extensible to any domain |

## Migration

None required. This adds new files and one new endpoint.
