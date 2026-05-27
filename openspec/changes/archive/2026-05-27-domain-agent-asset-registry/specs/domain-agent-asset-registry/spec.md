# domain-agent-asset-registry Specification

## ADDED Requirements

### Requirement: Domain agent manifests are discoverable
The system SHALL discover domain agent manifests from `backend/domain_agents/<agent_id>/agent.yaml` or `backend/domain_agents/<agent_id>/agent.yml`.

#### Scenario: Valid domain agent manifest is listed
- **GIVEN** a manifest under `backend/domain_agents/ecommerce_support/agent.yaml`
- **AND** the manifest includes `id`, `name`, `version`, and at least one `roles[].id`
- **WHEN** the domain agent registry contract is built
- **THEN** the contract includes an agent with `id = ecommerce_support`
- **AND** the agent includes normalized `roles`, `capabilities`, `governance`, `agent_dir`, and `manifest_path`
- **AND** the agent status is `ready`

### Requirement: Invalid manifests fail closed without blocking other agents
The system SHALL mark manifests with missing required fields as invalid and include a compact error entry.

#### Scenario: Missing required fields are reported
- **GIVEN** a domain agent manifest missing `name`
- **WHEN** the domain agent registry contract is built
- **THEN** the registry contract status is `degraded`
- **AND** `invalid_agents` is incremented
- **AND** `errors` includes the manifest path and missing field name

### Requirement: Empty registry has a stable contract
The system SHALL return a stable empty contract when no domain agent manifests exist.

#### Scenario: No manifests exist
- **GIVEN** the domain agent root exists but has no `agent.yaml` or `agent.yml`
- **WHEN** the domain agent registry contract is built
- **THEN** `status = empty`
- **AND** `total_agents = 0`
- **AND** `agents = []`
- **AND** `errors = []`

### Requirement: Runtime Surface exposes domain agent registry
The Runtime Surface profile SHALL expose the domain agent registry contract as `domain_agent_registry`.

#### Scenario: Frontend reads domain agent assets from Runtime Surface
- **WHEN** the Runtime Surface profile is assembled
- **THEN** the returned profile includes `domain_agent_registry`
- **AND** `domain_agent_registry.contract_version = domain-agent-registry-v1`
