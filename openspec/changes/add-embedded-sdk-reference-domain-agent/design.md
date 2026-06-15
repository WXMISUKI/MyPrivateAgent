# Design: Embedded SDK Reference Domain Agent

## Context

The Embedded SDK has been proven end-to-end with mock and real LLM providers. But no reference implementation shows how a domain project would use the SDK. The existing demos use the production `/api/chat` path, not the SDK path.

## Goals

1. Create a simple, self-contained domain agent ("天气助手") that uses `AgentHarnessFacade` with the SDK path.
2. Register real tools via `register_tool()` and demonstrate tool execution through the SDK loop.
3. Use `build_provider_model_step()` for LLM calls.
4. Capture and display governance trace as evidence.
5. Keep the example simple enough for domain projects to copy and modify.

## Non-Goals

1. No production chat path integration.
2. No persistence/recovery.
3. No streaming.
4. No child executor.
5. No frontend changes.

## Key Decisions

### Decision 1: Weather domain as reference

Weather is a well-understood domain with clear tool boundaries (query weather, query forecast). It's simple enough to be a reference but complex enough to demonstrate tool execution, model interaction, and governance trace.

### Decision 2: Simple tool implementations (no real API calls)

The reference agent uses deterministic mock tools (return hardcoded weather data) rather than calling real weather APIs. This keeps the example self-contained and runnable without external dependencies. Domain projects can replace these with real API calls.

### Decision 3: Facade as entry point

The reference agent uses `AgentHarnessFacade` (not raw `EmbeddedAgentRuntimeSDK`) because:
- It's the developer-facing entry point
- It exercises the full stack including tool registration and model_name auto-build
- It's what domain projects would use

### Decision 4: Multi-turn tool calling

The reference agent demonstrates multi-turn interaction: the model generates a response, decides to call a tool, the tool executes, and the model generates a final response with the tool result. This is the core agent loop pattern.

## Risks

| Risk | Mitigation |
|------|-----------|
| Example may become outdated as SDK evolves | Tests validate the example works |
| Domain projects may copy the example verbatim | Clear comments explain what to customize |

## Migration

None required. This adds examples and tests only.
