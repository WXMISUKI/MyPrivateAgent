# Design

## Boundary

The linkage evaluator is a caller-side governance helper. It reads already-available contracts and never mutates registries.

Inputs:

- domain agent catalog entry or normalized registry agent
- `ToolRuntimeService.build_runtime_contract()`
- `SkillRuntimeService.build_runtime_contract()`
- `McpRegistryService.list_servers()`

Outputs:

- `contract_version = domain-agent-capability-linkage-readiness-v1`
- `status`: `ready`, `review`, `blocked`, or `not_checked`
- declared/resolved/missing lists for tools, skills, MCP servers, and MCP capability references
- external knowledge source posture for RAG and graph declarations
- `recommended_action`

## Matching Rules

Tool linkage:

- declared `capabilities.tools[]` is matched against `tool_runtime.tools[].name`

Skill linkage:

- declared `capabilities.skills[]` is matched against `skill_contract.definitions[].name`

MCP linkage:

- declared `capabilities.mcp_servers[]` is matched against configured MCP server names and MCP capability names.
- This lets manifests declare either a configured MCP server name or a capability id, matching the existing lightweight manifest convention.

Knowledge linkage:

- `rag_sources` and `graph_sources` remain external-provider declarations.
- This service reports them as `not_checked` with `owner = external_provider`.

## Status Rules

- `ready`: all declared Tool, Skill, and MCP references are resolved, or no local capability references were declared.
- `review`: at least one declared Tool, Skill, or MCP reference is missing.
- `blocked`: reserved for invalid input or future required-capability rules; this change should not turn normal missing optional references into hard blockers.
- `not_checked`: used for external RAG/Graph source checks only.

## Integration

`DomainAgentCatalogService` receives an optional linkage service. When present, each catalog agent includes `capability_linkage`. The default service factory wires the linkage service to current ToolRuntime, SkillRuntime, and MCP runtime services.

The existing catalog fields remain stable. `capability_linkage` is additive and remains read-only.
