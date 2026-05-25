# ii3-embedded-sdk-tool-registration-bridge

## Why

`AgentHarnessFacade.register_tool()` already registers ToolSpec metadata into the tool runtime registry, but `EmbeddedAgentRuntimeSDK.register_tool()` is still a draft boundary. That leaves vertical integrations with two different tool registration stories: facade users can register tools, while SDK users cannot.

This change promotes SDK tool registration into the same backend runtime contract without creating a second tool runtime core.

## What Changes

- Implement `EmbeddedAgentRuntimeSDK.register_tool(...)` as a preview method.
- Normalize dict input into `ToolSpec` metadata.
- Register ToolSpec metadata with the configured `ToolRuntimeService.tool_registry`.
- Optionally register an executable handler as a runtime tool when supplied by embedded callers.
- Return a machine-readable registration contract including runtime registry status and executable binding status.
- Keep validation fail-closed for missing name/description.

## Out of Scope

- Async sandboxing or container isolation.
- Persistent callable serialization.
- External framework adapter registration.
- Frontend governance UI changes.
