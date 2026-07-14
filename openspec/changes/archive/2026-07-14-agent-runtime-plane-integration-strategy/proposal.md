## Why

MyPrivateAgent has reached a point where its control-plane contracts are much richer than its production execution-plane story. To avoid turning the project into a self-built replacement for LangGraph, AgentRun, ADK, OpenAI Agents SDK, or similar mature runtimes, this change defines a bounded runtime-plane integration strategy: use mature execution/runtime infrastructure through adapters while keeping agent assets, governance, approval, trace, audit, and contract gates under MyPrivateAgent control.

This is needed now because the project already has preview harness, embedded SDK, framework adapter, query control, domain agent registry, provider management, and workflow registry surfaces. Without a clear integration strategy, future work can easily keep expanding local harness/runtime pieces until the control plane becomes an unmaintainable platform clone.

## What Changes

- Add a formal runtime-plane integration strategy that separates:
  - AgentRun or equivalent managed runtime infrastructure.
  - LangGraph / ADK / OpenAI Agents SDK style execution orchestration.
  - MyPrivateAgent control-plane governance contracts.
- Define the first-class boundary between `control_plane`, `runtime_plane`, `framework_adapters`, `domain_agents`, and `capability_runtime`.
- Establish an `ExecutionAdapter v1` concept for normalizing external runtime requests, events, results, errors, approval interrupts, and trace references.
- Establish phased adoption:
  - Stage 0: freeze and close current control-plane positioning.
  - Stage 1: build three minimal runtime-plane vertical slices through adapters.
  - Stage 2: connect read-only governance and approval bridge.
  - Stage 3: harden templates, quality gates, and promotion rules.
- Add development constraints that prevent platform sprawl:
  - No self-built general checkpoint engine.
  - No self-built cloud sandbox/runtime platform.
  - No direct framework-native payloads in front-end governance contracts.
  - No production promotion without OpenSpec, adapter mapping, and gate evidence.
- Update project docs so new work has a single recommended direction and a clear stop line for local harness/runtime expansion.

Non-goals:

- Do not implement AgentRun, LangGraph, ADK, or OpenAI Agents SDK integration in this change.
- Do not move existing Python modules in bulk.
- Do not promote `AgentHarnessFacade` to production execution runtime.
- Do not change default `/api/chat` execution behavior.
- Do not introduce a new low-code workflow builder.
- Do not replace existing control-plane contracts, Runtime Surface, or Governance Timeline.

## Capabilities

### New Capabilities

- `runtime-plane-integration-strategy`: Defines how MyPrivateAgent uses mature execution/runtime systems through adapters while preserving local control-plane governance and development constraints.

### Modified Capabilities

- `agent-runtime-control-plane-positioning`: Clarifies that MyPrivateAgent owns control-plane contracts and should not continue expanding into a general production execution platform.
- `framework-adapter-authoring-checklist`: Extends adapter readiness expectations to include runtime-plane integration mapping, external runtime ownership, normalized execution envelopes, and promotion gates.

## Impact

Affected docs and specs:

- `docs/architecture/agent_runtime_control_plane_entrypoint.md`
- `docs/architecture/current_architecture.md`
- `docs/architecture/project_core_overview.md`
- `docs/architecture/reference_project_mapping.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
- `openspec/specs/agent-runtime-control-plane-positioning/spec.md`
- `openspec/specs/framework-adapter-authoring-checklist/spec.md`
- New spec: `openspec/specs/runtime-plane-integration-strategy/spec.md`

Affected implementation areas in later changes:

- `backend/agent_framework/framework_adapter_spi/`
- `backend/services/framework_adapter_runtime_service.py`
- `backend/services/query_control_plane_service.py`
- `backend/domain_agents/*/agent.yaml`
- Future `backend/runtime_plane/` and `backend/framework_adapters/` directories if/when implementation starts.

External references:

- Borrow from AgentRun: managed runtime infrastructure, sandbox, model/tool operations, observability, and deployment posture.
- Borrow from LangGraph: graph/state/checkpoint/human-in-loop execution semantics.
- Borrow from ADK / A2A / Agent Registry patterns: agent identity, discovery, and cross-agent boundary concepts.
- Borrow from OpenAI Agents SDK: handoff, guardrail, session, tracing, and tool-call event normalization ideas.
- Do not borrow their raw object model as the MyPrivateAgent public governance contract.
