# framework-adapter-authoring-checklist Specification

## Purpose

Define the side-effect-free authoring checklist and conservative promotion review contract for external framework adapters.
## Requirements
### Requirement: Framework adapter checklist is machine-readable
The system SHALL expose a side-effect-free framework adapter authoring checklist for a requested adapter candidate.

#### Scenario: Checklist is generated for a registered adapter
- **WHEN** a registered adapter id is reviewed
- **THEN** the checklist includes adapter identity, lifecycle mapping, readiness checks, governance timeline requirements, promotion gate, non-goals, and runtime-plane ownership boundaries
- **AND** the checklist includes `default_chat_entry = disabled`
- **AND** the checklist does not execute the adapter, call an external framework, mutate trace/audit state, or change `/api/chat`

#### Scenario: Checklist blocks unknown adapter
- **WHEN** an unknown adapter id is reviewed
- **THEN** the checklist status is `blocked`
- **AND** the result includes a machine-readable blocker for `adapter_not_registered`

### Requirement: Framework adapter promotion review is conservative
The system SHALL summarize whether an adapter candidate can proceed to a controlled pilot without promoting it into default main chat execution.

#### Scenario: Adapter precheck is ready

- **WHEN** adapter precheck evidence reports `ready = true`
- **THEN** the promotion review may report `pilot_candidate`
- **AND** `will_execute` remains `false`
- **AND** `default_chat_entry` remains `disabled`

#### Scenario: Adapter precheck is blocked

- **WHEN** adapter precheck evidence reports `ready = false`
- **THEN** the promotion review status is `blocked`
- **AND** the review includes missing packages, missing environment variables, or execution block reason when available

### Requirement: Checklist preserves adapter authoring boundaries
The framework adapter checklist SHALL NOT replace the Framework Adapter SPI, precheck, runtime pilot, external pilot, or Query Control mapping contracts.

#### Scenario: Checklist is consumed by a reviewer
- **WHEN** a reviewer inspects the checklist
- **THEN** the checklist points to required authoring sections and runtime-plane ownership boundaries
- **AND** it does not create a new adapter, register tools, invoke workers, modify provider bindings, or promote query detail/history/workspace layers

### Requirement: Checklist must encode runtime-plane integration constraints
The system SHALL require the adapter checklist to state whether the candidate is a runtime-plane dependency, a managed runtime target, or a control-plane-only integration.

#### Scenario: Reviewer assesses a runtime candidate

- **WHEN** a reviewer inspects an adapter candidate for AgentRun or LangGraph
- **THEN** the checklist MUST identify the candidate's runtime-plane role
- **AND** it MUST state which local contracts will receive normalized events, results, and interruptions
- **AND** it MUST state which control-plane surfaces remain unchanged

### Requirement: Framework adapter checklist includes authoring template
The framework adapter checklist SHALL include a machine-readable authoring template that turns the runtime-plane proof into repeatable adapter development guidance.

#### Scenario: Template is generated for a registered adapter
- **WHEN** a registered adapter id is reviewed
- **THEN** the checklist includes `authoring_template`
- **AND** the template includes template version, target framework, recommended files, required contracts, runtime-plane proof mapping, projection mapping, minimum smoke tests, promotion gate requirements, non-goals, and boundary flags
- **AND** the template includes `default_chat_entry = disabled`
- **AND** the checklist does not execute the adapter, call an external framework, mutate trace/audit state, register tools, or change `/api/chat`

#### Scenario: Template guides Stage 1 runtime-plane mapping
- **WHEN** a reviewer inspects the authoring template
- **THEN** the template maps `simple_agent`, `tool_agent`, and `approval_agent` proof slices to the adapter responsibilities they validate
- **AND** it identifies `runtime_plane_governance_profile` as the control-plane read model that may consume normalized projection evidence
- **AND** it states that this mapping is guidance for future adapters, not production runtime promotion

#### Scenario: Template is present for unknown adapter review
- **WHEN** an unknown adapter id is reviewed
- **THEN** the checklist status is `blocked`
- **AND** the result includes a machine-readable blocker for `adapter_not_registered`
- **AND** the result still includes authoring template guidance with registration-first next action and disabled execution boundaries
