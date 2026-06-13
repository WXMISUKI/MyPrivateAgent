## ADDED Requirements

### Requirement: Package dry-run preserves provider readiness
The grounded-answer package dry-run SHALL preserve compact provider readiness evidence from the input trial report when that evidence is present.

#### Scenario: Ready trial carries provider readiness into package
- **WHEN** the grounded-answer trial status is `go`
- **AND** the trial report includes `provider_readiness.status = ready`
- **THEN** the package status is `ready`
- **AND** the package includes the same compact provider readiness summary
- **AND** the package does not call the provider, chat, model, tools, memory, audit, trace, or source binding

#### Scenario: Review trial preserves provider warning
- **WHEN** the grounded-answer trial status is `review`
- **AND** the trial report includes provider readiness warnings such as source catalog degradation
- **THEN** the package status is `review`
- **AND** the package preserves provider readiness warnings

#### Scenario: Blocked trial preserves provider blocker
- **WHEN** the grounded-answer trial status is `blocked`
- **AND** the trial report includes provider readiness blockers such as provider unreachable
- **THEN** the package status is `blocked`
- **AND** the package preserves machine-readable provider blockers

#### Scenario: Graph boundary remains blocked
- **WHEN** the grounded-answer trial status is `blocked`
- **AND** the trial report includes `provider_readiness.graph_query_status = gated`
- **THEN** the package status is `blocked`
- **AND** the package preserves the GraphRAG promotion boundary
- **AND** document RAG readiness is not treated as GraphRAG execution readiness
