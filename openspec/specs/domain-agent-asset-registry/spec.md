# domain-agent-asset-registry Specification

## Purpose
TBD - created by archiving change domain-agent-asset-registry. Update Purpose after archive.
## Requirements
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

### Requirement: Domain agent manifests expose graph sources
The domain agent registry SHALL preserve knowledge graph source declarations from domain agent manifests.

#### Scenario: Valid graph source list is listed
- **GIVEN** a manifest under `backend/domain_agents/ecommerce_support/agent.yaml`
- **AND** the manifest includes `capabilities.graph_sources`
- **WHEN** the domain agent registry contract is built
- **THEN** the agent capabilities include normalized `graph_sources`
- **AND** invalid or empty graph source values are omitted

### Requirement: Domain agent manifests document retrieval policy
Domain agent manifests SHALL support documented knowledge retrieval policy for agents that bind RAG or graph sources.

#### Scenario: Agent declares retrieval policy
- **GIVEN** a domain agent manifest declares `capabilities.rag_sources` or `capabilities.graph_sources`
- **WHEN** a developer inspects the manifest
- **THEN** the manifest can include a `retrieval` section describing mode, citation requirement, fallback policy, and default retrieval limits

### Requirement: Domain agent prompt assets separate role from provider data
Domain agent assets SHALL keep role behavior and retrieval behavior in domain-agent prompts or policy files, not in the external provider source catalog.

#### Scenario: Agent defines knowledge behavior
- **GIVEN** a domain agent uses external RAG or graph sources
- **WHEN** its prompts are authored
- **THEN** prompts describe role boundaries, evidence usage, and fallback behavior
- **AND** provider source configuration remains limited to data, index, and retrieval metadata

### Requirement: Domain agent manifests expose grounding policy readiness
The domain agent registry SHALL preserve normalized grounding policy and grounding readiness details from domain agent manifests.

#### Scenario: Agent has grounding policy
- **WHEN** a domain agent manifest declares `grounding_policy`
- **THEN** the normalized agent contract includes `grounding_policy`
- **AND** the normalized agent contract includes `grounding_policy_status`

#### Scenario: Grounding policy registry is assembled
- **WHEN** the domain agent registry contract is built
- **THEN** it includes `grounding_policy_registry`
- **AND** the registry remains `visibility_only`

### Requirement: Domain agent manifests may reference Coze migration workflows
Domain agent manifests SHALL be able to reference Coze migration workflow capabilities without owning their execution implementation.

#### Scenario: Domain agent links to Coze workflow capability
- **GIVEN** a domain agent manifest declares `capabilities.coze_workflows`
- **WHEN** the domain agent registry contract is built
- **THEN** the normalized agent contract includes compact Coze workflow references
- **AND** each reference includes workflow id or capability id
- **AND** execution readiness remains delegated to the Coze migration workflow registry

#### Scenario: Domain agent cannot auto-execute workflow by reference
- **GIVEN** a domain agent references a Coze migration workflow
- **WHEN** the domain agent registry is inspected
- **THEN** the registry MUST NOT execute the workflow
- **AND** the registry MUST NOT auto-register a tool outside the unified workflow or capability runtime

### Requirement: Coze workflow references must fail closed when missing
The domain agent registry SHALL report missing Coze workflow references as readiness warnings or blockers without blocking unrelated agents.

#### Scenario: Referenced workflow does not exist
- **GIVEN** a domain agent references `customer_intake`
- **AND** no matching Coze workflow manifest exists
- **WHEN** the domain agent registry contract is built
- **THEN** the agent contract includes a missing workflow reference warning
- **AND** unrelated domain agents remain discoverable

