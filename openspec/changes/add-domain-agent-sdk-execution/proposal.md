# Proposal: Domain Agent SDK Execution Integration

## Background

The Embedded SDK path has been proven end-to-end (model_step → tool_executor → reviewer → governance trace). A reference domain agent ("天气助手") exists in `examples/weather_sdk_agent.py`. However, the SDK path is completely disconnected from the production system:

- The domain agent catalog (`/api/agents`) is read-only and manifest-driven — it does not execute agents
- The chat endpoint (`/api/chat`) uses `SimplifiedOrchestrator`, not the SDK path
- No API endpoint exists that executes domain agents through the SDK path

This means domain agents are governance-visible but not execution-capable through the system.

## Purpose

Create a domain agent execution integration that:

1. Registers the weather assistant in the domain agent catalog via `agent.yaml`
2. Creates a `DomainAgentExecutionService` that maps agent manifests to `AgentHarnessFacade` instances
3. Adds a `POST /api/agents/{agent_id}/execute` endpoint that executes domain agents through the SDK path
4. Returns governance trace as part of the response

This proves the SDK path integrates with the real system and creates a foundation for domain agent routing.

## Scope

- NEW: `backend/domain_agents/weather_assistant/agent.yaml` — domain agent manifest
- NEW: `backend/domain_agents/weather_assistant/tools.py` — weather tool implementations
- NEW: `backend/services/domain_agent_execution_service.py` — maps agent manifest to SDK facade
- NEW: `POST /api/agents/{agent_id}/execute` endpoint in `backend/routers/domain_agents.py`
- NEW: `tests/agent_framework/test_domain_agent_execution.py` — deterministic tests
- MODIFIED: Runtime contracts and roadmap docs

## Non-Goals

- No changes to the existing `/api/chat` endpoint
- No persistence/recovery
- No streaming (SDK path stays synchronous)
- No child executor
- No frontend changes
- No new provider backends

## Capabilities Affected

- NEW: `domain-agent-sdk-execution`

## Impact

- Backend: new domain agent manifest, new service, new endpoint, tests, docs
- No external API, DB schema, frontend, or default behavior changes
