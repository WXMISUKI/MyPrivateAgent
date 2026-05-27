## ADDED Requirements

### Requirement: Domain agent manifests expose graph sources
The domain agent registry SHALL preserve knowledge graph source declarations from domain agent manifests.

#### Scenario: Valid graph source list is listed
- **GIVEN** a manifest under `backend/domain_agents/ecommerce_support/agent.yaml`
- **AND** the manifest includes `capabilities.graph_sources`
- **WHEN** the domain agent registry contract is built
- **THEN** the agent capabilities include normalized `graph_sources`
- **AND** invalid or empty graph source values are omitted

