## Why

MyPrivateAgent has accumulated stable runtime contracts, provider onboarding gates, domain-agent trial surfaces, Embedded SDK seams, and framework adapter boundaries. The repository still starts from a broad docs index, so maintainers and external project owners must know which documents to read before they can pick the correct integration path.

This change productizes the documentation entrypoint so a reader can start from `docs/README.md`, understand the Agent Runtime Control Plane positioning, and choose the right seam without reading historical change logs.

## What Changes

- Promote `docs/README.md` from a broad index into the current control-plane entrypoint.
- Update the architecture entrypoint and checklist with the current four integration paths:
  - external providers
  - domain agents
  - Embedded SDK / Agent Harness
  - framework adapters
- Make ready/gated/non-goal boundaries visible at the entrypoint level.
- Sync canonical entrypoint specs and roadmap state.

Non-goals:

- Do not change backend runtime code.
- Do not change frontend behavior.
- Do not invoke providers, tools, MCP, chat, memory, trace, audit, or source binding.
- Do not promote default chat grounding, GraphRAG, provider execution, or framework adapters.

## Capabilities

### Modified Capabilities

- `agent-runtime-control-plane-entrypoint-readiness`: Productizes repository entrypoint docs and task-oriented checklist.
- `agent-runtime-control-plane-positioning`: Keeps the official control-plane positioning visible from the repository entrypoint.

## Impact

- Docs:
  - `docs/README.md`
  - `docs/architecture/agent_runtime_control_plane_entrypoint.md`
  - `docs/guides/project_entrypoint_checklist.md`
  - `docs/architecture/current_architecture.md`
  - `docs/architecture/extension_points.md`
  - `docs/roadmap/next_phase_hardening.md`
- Specs:
  - `openspec/specs/agent-runtime-control-plane-entrypoint-readiness/spec.md`
  - optional positioning note if needed.
