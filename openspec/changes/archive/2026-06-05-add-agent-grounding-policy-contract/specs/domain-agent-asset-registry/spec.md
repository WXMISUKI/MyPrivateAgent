## ADDED Requirements

### Requirement: Domain agent manifests expose grounding policy
The domain agent registry SHALL preserve normalized grounding policy declarations from domain agent manifests.

#### Scenario: Manifest includes grounding policy
- **GIVEN** a manifest under `backend/domain_agents/ecommerce_support/agent.yaml`
- **AND** the manifest includes `grounding_policy.require_citations`
- **WHEN** the domain agent registry contract is built
- **THEN** the agent includes normalized `grounding_policy`
- **AND** invalid or empty grounding policy values are omitted or reported without blocking other valid manifest fields

#### Scenario: Runtime Surface exposes domain agent grounding policy
- **WHEN** the Runtime Surface profile is assembled
- **THEN** `domain_agent_registry.agents[]` includes normalized grounding policy data for agents that declare it
- **AND** existing `rag_source_registry` and `knowledge_graph_registry` contracts remain stable
