## ADDED Requirements

### Requirement: External provider guidance preserves runtime boundary
The external knowledge provider guidance SHALL keep implementation dependencies and data lifecycle concerns outside MyPrivateAgent core runtime.

#### Scenario: Provider uses LlamaIndex
- **WHEN** the external provider implements document RAG with LlamaIndex
- **THEN** MyPrivateAgent invokes it only through provider-neutral HTTP capability contracts
- **AND** MyPrivateAgent does not import LlamaIndex modules

#### Scenario: Provider uses Neo4j GraphRAG
- **WHEN** the external provider implements graph retrieval with Neo4j GraphRAG
- **THEN** MyPrivateAgent invokes it only through provider-neutral HTTP capability contracts
- **AND** MyPrivateAgent does not import Neo4j or graph retriever modules

### Requirement: Knowledge provider catalog supports readiness checks
The external knowledge provider SHALL expose enough source catalog metadata for MyPrivateAgent governance surfaces to identify missing or degraded source bindings.

#### Scenario: Declared source is unavailable
- **WHEN** a domain agent declares a source id that the provider does not expose as ready
- **THEN** provider capability or heartbeat responses include a machine-readable missing or degraded status
- **AND** MyPrivateAgent can surface the condition without blocking application startup
