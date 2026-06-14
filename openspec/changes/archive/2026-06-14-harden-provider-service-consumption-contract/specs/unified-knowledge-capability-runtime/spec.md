## ADDED Requirements

### Requirement: Knowledge provider feeds generic provider consumption
The unified knowledge capability runtime SHALL provide compact readiness input to the generic provider service consumption contract without changing existing knowledge capability behavior.

#### Scenario: Knowledge provider is configured
- **WHEN** `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true`
- **AND** `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL` is set
- **THEN** the generic provider management contract includes a knowledge provider entry
- **AND** the entry references `knowledge.rag.retrieve` and `knowledge.graph.query` from the existing capability runtime

#### Scenario: Knowledge provider readiness is consumed
- **WHEN** knowledge capability health or heartbeat includes `governance_readiness`
- **THEN** the generic provider readiness model consumes its compact status, source catalog posture, GraphRAG gate, and default chat grounding gate
- **AND** it does not copy raw provider health payloads, retrieved evidence, or answer text

#### Scenario: Knowledge provider management preserves boundaries
- **WHEN** the generic provider contract reports the knowledge provider as ready
- **THEN** explicit RAG retrieval may be invoked through the provider/capability management path
- **AND** default `/api/chat` retrieval injection remains disabled
- **AND** GraphRAG execution and source-to-agent binding automation remain gated
