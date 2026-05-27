## Why

The project needs a formal positioning decision after evaluating mature agent frameworks such as LangGraph, OpenAI Agents SDK, Qwen-Agent, CrewAI, AutoGen/Microsoft Agent Framework, DeerFlow, and Agno. These frameworks should be treated as execution engines or reference implementations, while MyPrivateAgent should own the enterprise runtime control plane: governance, contracts, adapters, permissions, audit, observability, and business-system integration.

Without this decision, future work may keep drifting between "build another agent framework" and "bind the product to one external framework", both of which would weaken the current Runtime Core, ToolRuntime, Query Control, Governance Timeline, and OpenSpec investment.

## What Changes

- Confirm MyPrivateAgent's official project positioning as an enterprise Agent Runtime Control Plane, not a replacement for external agent frameworks.
- Establish that external frameworks are pluggable execution adapters below the local Runtime Core / Governance / Capability contracts.
- Update roadmap, architecture, OpenSpec context, and reference mapping documents so future changes inherit the same positioning.
- Add a canonical OpenSpec capability for project positioning and framework-adapter boundaries.
- Reframe the next development sequence around specification, implementation, archive, and git submission gates.
- Record current follow-up priorities from existing specs and archived changes without starting new runtime implementation in this change.

收口对象:

- Project positioning
- External framework adapter boundary
- Runtime Control Plane responsibility
- Documentation/spec workflow for future framework integrations

非目标:

- Do not migrate the current runtime to LangGraph, CrewAI, Qwen-Agent, DeerFlow, OpenAI Agents SDK, or any single external framework.
- Do not implement a new framework adapter in this change.
- Do not change backend runtime contract payloads or frontend governance UI behavior in this change.
- Do not enable external adapters in the main chat execution path by default.

## Capabilities

### New Capabilities

- `agent-runtime-control-plane-positioning`: Defines MyPrivateAgent as the enterprise control plane above pluggable agent execution frameworks.

### Modified Capabilities

- `runtime-harness-reference-alignment`: Clarify that production agent frameworks are execution-engine references and adapter candidates, not project-level architectural replacements.

## Impact

Affected code:

- None. This is a documentation and specification alignment change.

Affected backend contracts:

- No payload shape change.
- Future framework integration changes must preserve `RuntimeSurfaceService`, `ToolRuntimeService`, `QueryControlPlane`, `RuntimeContractGate`, and Governance Timeline contracts as the local truth source.

Affected frontend consumption points:

- No UI behavior change.
- Future adapter UI work must consume runtime/governance contracts instead of framework-specific raw payloads.

Affected docs/specs:

- `openspec/config.yaml`
- `openspec/README.md`
- `openspec/specs/agent-runtime-control-plane-positioning/spec.md`
- `openspec/specs/runtime-harness-reference-alignment/spec.md`
- `docs/architecture/runtime_contracts.md`
- `docs/architecture/reference_project_mapping.md`
- `docs/roadmap/next_phase_hardening.md`
