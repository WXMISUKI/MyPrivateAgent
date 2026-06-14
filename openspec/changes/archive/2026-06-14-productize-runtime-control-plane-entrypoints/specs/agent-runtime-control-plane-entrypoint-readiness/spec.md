## ADDED Requirements

### Requirement: Repository README acts as the current control-plane entrypoint
The repository docs README SHALL provide a task-oriented current entrypoint before historical or broad index material.

#### Scenario: Reader enters through docs README
- **WHEN** a maintainer opens `docs/README.md`
- **THEN** the first section identifies MyPrivateAgent as an Agent Runtime Control Plane
- **AND** it directs readers to current architecture, runtime contracts, extension points, provider onboarding, domain-agent development, Embedded SDK, framework adapter guidance, and roadmap documents
- **AND** it does not require reading `docs/change` first

### Requirement: Entrypoint docs expose integration path boundaries
The entrypoint docs SHALL make the main integration paths and their ready/gated boundaries visible.

#### Scenario: Reader chooses an external provider path
- **WHEN** a reader wants to connect an external provider
- **THEN** the entrypoint points to provider onboarding catalog, service-provider management, provider onboarding UI, acceptance gate, and capability runtime guide
- **AND** it states that accepted providers remain explicit managed-provider consumption only

#### Scenario: Reader chooses a framework adapter path
- **WHEN** a reader wants to add or evaluate an external framework adapter
- **THEN** the entrypoint points to adapter authoring checklist, precheck, pilot, lifecycle mapping, and promotion gate guidance
- **AND** it states that adapters remain disabled from default main-chat execution until explicit promotion

#### Scenario: Reader chooses Embedded SDK or domain-agent path
- **WHEN** a reader wants to integrate through Embedded SDK or a domain agent
- **THEN** the entrypoint points to the corresponding SDK/harness or domain-agent seam
- **AND** it states which trial or smoke command proves readiness without promoting default chat behavior

### Requirement: Entrypoint productization remains documentation-only
The entrypoint productization change SHALL NOT mutate runtime behavior.

#### Scenario: Entrypoint docs are productized
- **WHEN** the docs entrypoint, checklist, architecture notes, and roadmap are updated
- **THEN** no backend runtime code, frontend behavior, provider invocation, tool execution, memory write, audit write, trace write, source binding, or `/api/chat` behavior is changed
- **AND** strict OpenSpec validation remains passing
