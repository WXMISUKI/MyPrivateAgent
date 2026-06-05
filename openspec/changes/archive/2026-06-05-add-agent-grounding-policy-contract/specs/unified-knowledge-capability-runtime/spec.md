## ADDED Requirements

### Requirement: Knowledge readiness can inform grounding policy
The knowledge capability runtime SHALL expose enough readiness data for grounding policy surfaces to explain missing or degraded knowledge sources without changing provider-neutral invocation contracts.

#### Scenario: Grounding policy references knowledge sources
- **WHEN** an agent grounding policy requires citations or restricts source ACL mode
- **THEN** MyPrivateAgent can compare the agent manifest's source declarations with knowledge capability readiness data
- **AND** it can report missing, unknown, or degraded readiness without importing provider-specific RAG or GraphRAG dependencies

#### Scenario: Knowledge provider is absent
- **WHEN** no external knowledge provider is configured
- **THEN** grounding policy readiness can report provider availability as `unknown` or `not_configured`
- **AND** `/api/chat` and application startup remain unchanged
