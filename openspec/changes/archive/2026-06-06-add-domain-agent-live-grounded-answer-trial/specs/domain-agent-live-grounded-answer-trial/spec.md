## ADDED Requirements

### Requirement: Live grounded-answer trial invokes document RAG provider explicitly
The system SHALL provide an explicit domain-agent live grounded-answer trial that retrieves evidence from the configured external document RAG provider and feeds it into the existing grounded-answer trial chain.

#### Scenario: Live trial succeeds with answerable evidence
- **GIVEN** a domain agent exists with manifest-declared `rag_sources`
- **AND** the provider returns `documents` and `metadata.evidence_pack.status=answerable`
- **WHEN** the live trial runs for that agent and query
- **THEN** the report status is `go`
- **AND** the report includes provider retrieve summary, trial report, package dry-run, and composition trial output

#### Scenario: Live trial reviews insufficient evidence
- **GIVEN** the provider returns `metadata.evidence_pack.status=insufficient_evidence`
- **WHEN** the live trial runs
- **THEN** the report status is `review` or `blocked` according to the existing grounding and promotion rules
- **AND** the report includes a machine-readable reason code

#### Scenario: Live trial blocks provider failures
- **GIVEN** the provider is unreachable, returns invalid JSON, returns an HTTP error, or omits required retrieve fields
- **WHEN** the live trial runs
- **THEN** the report status is `blocked`
- **AND** the report identifies the provider recovery action

### Requirement: Live trial uses domain-agent manifest RAG scope
The live trial SHALL use the selected domain agent manifest as the source scope for provider retrieval.

#### Scenario: Agent has no RAG sources
- **GIVEN** a domain agent exists but declares no `rag_sources`
- **WHEN** the live trial runs
- **THEN** the report status is `blocked`
- **AND** no provider retrieve call is required

#### Scenario: Agent does not exist
- **GIVEN** the requested domain agent id is missing
- **WHEN** the live trial runs
- **THEN** the report status is `blocked`
- **AND** the report identifies `agent_not_found`

### Requirement: Live trial preserves caller and provider boundaries
The live trial SHALL remain explicit, read-only, and side-effect-free.

#### Scenario: Live trial runs
- **WHEN** a caller runs the live trial
- **THEN** it does not call `/api/chat`
- **AND** it does not create source-to-agent binding, write memory, write audit or trace records, execute tools, call GraphRAG, promote retrieval defaults, or enable default chat retrieval injection

#### Scenario: Provider returns graph boundary metadata
- **WHEN** the provider is document-RAG ready but graph execution remains planned
- **THEN** the live document RAG trial may proceed
- **AND** GraphRAG execution remains separately gated
