# Design

## Summary

This slice adds a small API-facing wrapper over the existing manifest registry:

- source of truth remains `DomainAgentRegistryService`
- new adapter service reshapes registry data into a stable catalog contract
- router exposes `GET /api/agents`

The wrapper is intentionally read-only and narrower than Runtime Surface. It should be easy for callers to consume without parsing unrelated runtime profile fields, while still preserving enough governance visibility to understand available agents and their declared capabilities.

## Contract Shape

The catalog returns:

- `contract_version`
- `status`
- `total_agents`
- `ready_agents`
- `invalid_agents`
- `agents`
- `errors`

Each ready agent entry should include:

- identity: `id`, `name`, `version`, `description`, `status`
- role summary: `roles`, `default_role_id`
- declared capabilities: `tools`, `skills`, `mcp_servers`, `rag_sources`, `graph_sources`
- capability counts for quick inspection
- compact grounding summary and grounding readiness summary

Unlike the lower-level registry, the catalog should avoid exposing filesystem-only details such as `root_path`, `agent_dir`, and `manifest_path` on successful agent entries. Invalid manifest errors may still include manifest path context because that is diagnostic evidence.

## Boundary

The new catalog service does not own manifest parsing rules. It consumes the already-normalized registry contract and maps it into an API wrapper.

This keeps responsibilities clear:

- `DomainAgentRegistryService` owns filesystem discovery and normalization
- `DomainAgentCatalogService` owns API-facing shaping
- router owns HTTP exposure

## Verification

Focused verification should cover:

- ready catalog shape from a ready registry
- empty catalog passthrough
- degraded catalog with invalid manifest errors
- `GET /api/agents` returns the wrapper contract

No chat behavior, runtime profile behavior, or tool registration behavior should change.
