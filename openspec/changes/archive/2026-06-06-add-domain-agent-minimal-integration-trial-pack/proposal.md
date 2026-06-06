# Domain Agent Minimal Integration Trial Pack

## Why

The domain-agent control-plane chain now has read-only catalog visibility, capability linkage readiness, grounded-answer trial, package dry-run, and composition trial. What is still missing is a minimal caller-facing trial pack that shows how a repo-side caller can run the chain end to end without learning each internal control surface separately.

This change turns the existing pieces into a lightweight, repeatable trial path. It is intended to help a caller decide `go / review / blocked` before attempting a real repository-side grounded-answer integration.

## What Changes

- Define a minimal integration trial pack contract for domain-agent repo-side trial readiness.
- Add a side-effect-free smoke script that runs the existing trial, package dry-run, and composition trial services from a compact JSON payload.
- Add a reusable example payload that documents the minimum evidence fields expected from the caller side.
- Document the endpoint and script sequence for external callers.

## Non-goals

- Do not add default `/api/chat` retrieval injection.
- Do not call a real Knowledge Provider, LLM, MCP server, tool, or external repository.
- Do not create source bindings, memory, audit, trace, prompt rollout, or approval state.
- Do not add agent enable/disable, marketplace, editing, multi-tenant policy, or production deployment workflows.
- Do not replace existing grounded-answer trial/package/composition services.

## Impact

- OpenSpec: add a canonical minimal integration trial pack spec.
- Backend scripts: add a focused repo-side smoke script.
- Docs/examples: add a caller payload and update the domain-agent guide.
- Tests: add focused tests around the smoke runner and status aggregation.
