# Domain Agent Manifest Capability Linkage Readiness

## Why

`GET /api/agents` now exposes a read-only domain agent catalog, but it only reports what each `agent.yaml` declares. The next useful governance step is to show whether declared Tool, Skill, and MCP capabilities can be recognized by the current MyPrivateAgent capability layer.

This keeps the domain agent catalog practical for callers without turning it into an agent marketplace or enabling runtime behavior.

## What Changes

- Add a read-only capability linkage readiness contract for domain agent manifests.
- Compare manifest-declared `tools`, `skills`, and `mcp_servers` against existing ToolRuntime, SkillRuntime, and MCP runtime contracts.
- Extend `GET /api/agents` catalog entries with compact linkage status, missing declarations, and recommended action.
- Keep RAG and Graph source declarations as external-provider references and mark them as `not_checked` by this MyPrivateAgent-side linkage gate.

## Non-goals

- Do not auto-register tools, skills, MCP servers, RAG sources, or graph sources.
- Do not add agent enable/disable, editing, marketplace workflows, approvals, or database state.
- Do not change `/api/chat`, default RAG injection, prompt activation, memory injection, or tool execution.
- Do not call the external knowledge provider or execute GraphRAG.

## Impact

- Backend service: add a read-only linkage readiness evaluator.
- Catalog API: extend `GET /api/agents` entries with `capability_linkage`.
- Specs/docs: record the read-only linkage boundary.
- Tests: add focused unit and router coverage.
