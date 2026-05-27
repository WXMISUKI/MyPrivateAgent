## ADDED Requirements

### Requirement: Knowledge capabilities are provider-neutral
The system SHALL expose RAG and knowledge graph capabilities through provider-neutral capability contracts without requiring vector store, graph database, embedding, reranker, OCR, or document parsing dependencies in the core backend.

#### Scenario: Registry lists knowledge capabilities
- **WHEN** an external knowledge provider is configured
- **THEN** `GET /api/capabilities` includes `knowledge.rag.retrieve` and `knowledge.graph.query`
- **AND** each capability includes `capability_id`, `kind`, `transport`, `provider`, `status`, `input_schema`, and `output_schema`

#### Scenario: Provider is not configured
- **WHEN** no external knowledge provider is configured
- **THEN** the main application starts normally
- **AND** the knowledge capabilities are absent from the default registry

### Requirement: RAG retrieval returns citation evidence
The system SHALL require RAG retrieval responses to include source-level citation evidence suitable for trace, audit, and user-facing attribution.

#### Scenario: RAG retrieve invocation succeeds
- **WHEN** a client invokes `POST /api/capabilities/knowledge.rag.retrieve/invoke`
- **THEN** the response includes a provider-neutral envelope
- **AND** the result includes `answer_context`
- **AND** each returned document includes `source_id`, `document_id`, `title`, `snippet`, `score`, and `citation`

#### Scenario: RAG provider is unavailable
- **WHEN** the configured RAG provider cannot be reached
- **THEN** the invoke or health response returns a structured provider error
- **AND** `/api/chat` and the main server remain healthy

### Requirement: Knowledge graph query returns graph evidence
The system SHALL expose knowledge graph query capability separately from RAG retrieval.

#### Scenario: Graph query invocation succeeds
- **WHEN** a client invokes `POST /api/capabilities/knowledge.graph.query/invoke`
- **THEN** the response includes a provider-neutral envelope
- **AND** the result includes `graph_id`, `entities`, `relations`, `paths`, and `evidence`

#### Scenario: Graph provider is unavailable
- **WHEN** the configured graph provider cannot be reached
- **THEN** the invoke or health response returns a structured provider error
- **AND** the main server remains healthy

### Requirement: Knowledge registries expose domain agent bindings
The Runtime Surface SHALL expose read-only knowledge registries derived from domain agent manifests.

#### Scenario: Domain agent declares RAG and graph sources
- **WHEN** a domain agent manifest declares `capabilities.rag_sources` or `capabilities.graph_sources`
- **THEN** Runtime Surface includes `rag_source_registry`
- **AND** Runtime Surface includes `knowledge_graph_registry`
- **AND** each registry entry includes the owning `agent_id`

#### Scenario: No domain agent declares knowledge sources
- **WHEN** no manifest declares RAG or graph sources
- **THEN** the registry contracts remain stable
- **AND** they report zero entries without blocking Runtime Surface assembly

### Requirement: External Knowledge Provider development contract is documented
The repository SHALL document how an external Knowledge Provider should be developed and integrated.

#### Scenario: Developer reads provider guide
- **WHEN** a developer opens the external RAG provider development guide
- **THEN** the guide describes project layout, minimum HTTP API, RAG request and response contracts, graph query contracts, health checks, and MyPrivateAgent environment wiring

