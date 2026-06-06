# Domain Agent Catalog Read-Only API

## Why

`DomainAgentRegistryService` and Runtime Surface already expose manifest-driven domain agent visibility, but callers still need to read that data through the broad runtime profile or internal service seams. The roadmap explicitly calls out a small follow-up slice around a read-only `GET /api/agents` wrapper instead of jumping straight to enable/disable, editing, or a full marketplace.

This change creates that wrapper so callers, governance tooling, and future integration work can read a stable agent catalog without depending on the whole Runtime Surface payload and without importing filesystem-oriented registry details directly.

## What Changes

- Add a read-only domain agent catalog service that adapts `domain_agent_registry` into a narrower API-facing contract.
- Add `GET /api/agents` as the first catalog wrapper endpoint.
- Keep the catalog manifest-driven and visibility-only.
- Sync domain agent documentation so the new catalog entry point is discoverable.

## Non-goals

- Do not add agent enable/disable, editing, creation, or deletion.
- Do not add `/api/agents/{agent_id}/chat` or alter `POST /api/chat`.
- Do not auto-register tools, skills, MCP servers, or knowledge sources from manifests.
- Do not add database persistence, marketplace workflows, approval flows, or asset mutation APIs.

## Impact

- Backend contract: add `domain-agent-catalog-v1` as a read-only API-facing wrapper over the existing registry.
- Router surface: add `GET /api/agents`.
- Documentation: update the domain agent guide and architecture notes.
- Tests: add focused router and service coverage for catalog shape and empty/degraded behavior.
