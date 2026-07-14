## ADDED Requirements

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
