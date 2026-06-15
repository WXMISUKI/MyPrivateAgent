# Proposal: Embedded SDK Reference Domain Agent

## Background

The Embedded SDK has been proven end-to-end: `model_step` → `tool_executor` → `reviewer` → governance trace works with real LLM providers. However, no reference implementation exists showing how a domain project would actually use the SDK to build an agent. The existing demos (`weather_demo_app.py`, `knowledge_demo_app.py`) use the production `/api/chat` path through `SimplifiedOrchestrator`, not the SDK path.

Without a reference implementation, domain projects have no concrete example to follow. The SDK's value proposition — "you bring the framework, we bring the governance" — remains theoretical.

## Purpose

Create a reference domain agent ("天气助手" / Weather Assistant) that uses the Embedded SDK path end-to-end:

```
AgentHarnessFacade(name="weather-agent", model_name="doubao")
  → register_tool("query_weather", handler=...)
  → execute(model_name="doubao")
  → build_provider_model_step → ExecutionLoopController
  → real LLM call → tool execution → governance trace
```

This serves as:
1. **Proof of concept**: demonstrates the SDK is usable by domain projects
2. **Reference implementation**: domain projects can copy, modify, extend
3. **Integration test target**: validates the full SDK path with real tools
4. **Documentation anchor**: concrete example for guides and tutorials

## Scope

- NEW: `examples/weather_sdk_agent.py` — reference domain agent using SDK path
- NEW: `tests/agent_framework/test_weather_sdk_agent.py` — deterministic tests for the reference agent
- NEW: Canonical spec `embedded-sdk-reference-domain-agent`
- MODIFIED: Runtime contracts and roadmap docs

## Non-Goals

- No changes to the existing `/api/chat` production path
- No persistence/recovery
- No streaming
- No child executor
- No new provider backends
- No frontend changes

## Capabilities Affected

- NEW: `embedded-sdk-reference-domain-agent`

## Impact

- Backend: new example script, new tests, docs
- No external API, DB schema, frontend, or default behavior changes
