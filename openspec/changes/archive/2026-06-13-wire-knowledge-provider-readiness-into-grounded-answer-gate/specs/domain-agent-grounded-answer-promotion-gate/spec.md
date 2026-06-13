## ADDED Requirements

### Requirement: Promotion gate consumes Knowledge Provider governance readiness
The grounded-answer promotion gate SHALL recognize Knowledge Provider `governance_readiness` as the preferred provider readiness evidence when it is present.

#### Scenario: Governance readiness allows document RAG trial promotion
- **WHEN** provider evidence includes `governance_readiness.rag_retrieve.status = ready`
- **AND** grounding, PromptOps, MemoryOps, and eval evidence satisfy the existing promotion requirements
- **THEN** the promotion gate SHALL treat provider readiness as ready for document RAG trial promotion
- **AND** the promotion gate SHALL preserve `default_chat_grounding.status = gated` as a behavior boundary rather than a blocker for repo-side trial

#### Scenario: Governance readiness blocks unreachable provider
- **WHEN** provider evidence includes `governance_readiness.overall_status = unreachable`
- **THEN** the promotion decision SHALL be `blocked`
- **AND** the blockers SHALL identify provider readiness as unreachable

#### Scenario: Governance readiness reviews degraded source catalog
- **WHEN** provider evidence includes `governance_readiness.source_catalog.status = degraded`
- **THEN** the promotion decision SHALL be `review` or `blocked`
- **AND** the output SHALL preserve a machine-readable provider catalog reason

### Requirement: GraphRAG gate uses governance readiness
The grounded-answer promotion gate SHALL preserve GraphRAG as separately gated when Knowledge Provider readiness reports `graph_query.status = gated`.

#### Scenario: Graph request is blocked despite RAG readiness
- **WHEN** a promotion decision requests graph usage
- **AND** provider evidence includes `governance_readiness.rag_retrieve.status = ready`
- **AND** `governance_readiness.graph_query.status = gated`
- **THEN** the promotion decision SHALL be `blocked`
- **AND** the blockers SHALL identify GraphRAG execution as not promoted

### Requirement: Promotion gate remains side-effect-free with provider readiness
Consuming Knowledge Provider governance readiness MUST NOT cause the promotion gate to invoke provider APIs or mutate runtime behavior.

#### Scenario: Readiness is consumed without side effects
- **WHEN** the promotion gate evaluates provider `governance_readiness`
- **THEN** no provider request SHALL be sent
- **AND** no answer SHALL be generated
- **AND** no source binding, memory, audit, trace, or chat state SHALL be mutated
- **AND** default `/api/chat` retrieval injection SHALL remain disabled
