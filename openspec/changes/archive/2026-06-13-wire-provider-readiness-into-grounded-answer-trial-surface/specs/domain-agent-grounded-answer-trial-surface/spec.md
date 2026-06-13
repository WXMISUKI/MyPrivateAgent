## ADDED Requirements

### Requirement: Trial surface preserves provider governance readiness
The grounded-answer trial surface SHALL preserve compact caller-supplied provider governance readiness evidence in the trial report when that evidence is present.

#### Scenario: Provider readiness supports trial go
- **WHEN** caller-supplied provider evidence includes `governance_readiness.rag_retrieve.status = ready`
- **AND** the grounded-answer promotion gate returns `go`
- **THEN** the trial report status is `go`
- **AND** the report includes a compact provider readiness summary
- **AND** the report does not call the provider, chat, model, tools, memory, audit, trace, or source binding

#### Scenario: Provider catalog degradation requires review
- **WHEN** caller-supplied provider evidence includes `governance_readiness.source_catalog.status = degraded`
- **AND** the grounded-answer promotion gate returns `review`
- **THEN** the trial report status is `review`
- **AND** the report includes provider readiness warnings that identify the degraded catalog posture

#### Scenario: Provider unreachable blocks trial
- **WHEN** caller-supplied provider evidence includes `governance_readiness.overall_status = unreachable`
- **AND** the grounded-answer promotion gate returns `blocked`
- **THEN** the trial report status is `blocked`
- **AND** the report includes machine-readable provider blockers

#### Scenario: Graph readiness remains gated
- **WHEN** caller-supplied provider evidence includes `governance_readiness.graph_query.status = gated`
- **AND** the trial request asks for graph grounding
- **THEN** the trial report status is `blocked`
- **AND** the report preserves the graph promotion boundary
- **AND** document RAG readiness is not treated as GraphRAG execution readiness
