# agent-runtime-control-plane-entrypoint-readiness Specification

## Purpose
TBD - created by archiving change add-agent-runtime-control-plane-entrypoint-readiness. Update Purpose after archive.
## Requirements
### Requirement: Repository exposes a current control-plane entrypoint
The repository SHALL provide a concise entrypoint document that explains the current Agent Runtime Control Plane positioning and directs readers to the correct deeper documents.

#### Scenario: New maintainer enters the repository
- **WHEN** a maintainer needs to understand the current project posture
- **THEN** the entrypoint document identifies MyPrivateAgent as an Agent Runtime Control Plane
- **AND** it links to current architecture, runtime contracts, extension points, domain-agent development, external provider guides, and the current roadmap
- **AND** it does not require reading historical change logs first

### Requirement: Repository exposes a task-oriented entrypoint checklist
The repository SHALL provide a checklist that maps common next actions to the correct verification and extension path.

#### Scenario: Caller wants to try a domain agent
- **WHEN** a caller wants to run a minimal domain-agent integration trial
- **THEN** the checklist points to `GET /api/agents`, `capability_linkage`, the grounded-answer trial endpoints, and `backend/scripts/domain_agent_trial_smoke.py`
- **AND** it states that this trial path does not promote default `/api/chat` retrieval injection

#### Scenario: Maintainer wants to extend runtime or adapters
- **WHEN** a maintainer wants to extend SDK, ToolRuntime, framework adapters, or provider integrations
- **THEN** the checklist directs them to the relevant extension seam and OpenSpec-first workflow
- **AND** it states the non-goals that must not be bypassed

### Requirement: Entrypoint docs preserve current behavior boundaries
The entrypoint readiness update SHALL remain documentation-only and SHALL NOT change runtime behavior.

#### Scenario: Entrypoint docs are updated
- **WHEN** the entrypoint and checklist are added
- **THEN** no backend runtime code, frontend behavior, provider invocation, tool execution, memory write, audit write, trace write, source binding, or `/api/chat` behavior is changed
- **AND** strict OpenSpec validation remains passing

