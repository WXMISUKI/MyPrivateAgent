## ADDED Requirements

### Requirement: Workflow Dependency Provider Readiness
The provider service consumption contract SHALL expose provider readiness in a form that workflow dependency mapping can consume.

#### Scenario: Workflow maps dependency to provider
- **WHEN** a workflow dependency maps to a provider-owned capability
- **THEN** the provider management surface exposes provider id, capability id, readiness status, blockers, warnings, onboarding path, and evidence preview path
- **AND** workflow dependency mapping can reference those fields without copying provider raw payloads.

#### Scenario: Provider readiness is blocked
- **WHEN** a required provider is unreachable, disabled, unconfigured, gated, or does not own the requested capability
- **THEN** workflow dependency mapping marks the dependency blocked
- **AND** includes a machine-readable provider blocker.

### Requirement: Provider Readiness Does Not Promote Default Chat
Provider readiness consumed by workflow dependency mapping SHALL NOT imply default chat grounding, source binding, GraphRAG execution, memory writes, audit writes, or final answer policy changes.

#### Scenario: Provider is ready for explicit workflow use
- **WHEN** a provider-backed dependency is ready for explicit capability invocation
- **THEN** the workflow may use it only through explicit capability invocation
- **AND** default `/api/chat` behavior remains unchanged.
