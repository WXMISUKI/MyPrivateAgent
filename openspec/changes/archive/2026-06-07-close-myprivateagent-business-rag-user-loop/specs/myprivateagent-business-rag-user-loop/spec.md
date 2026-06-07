# myprivateagent-business-rag-user-loop Specification

## ADDED Requirements

### Requirement: Business RAG user-loop closure summarizes local trial readiness

The system SHALL provide an explicit local closure report for the MyPrivateAgent business RAG user loop.

#### Scenario: Closure returns go
- **GIVEN** the local knowledge provider corpus trial artifact exists with decision `go`
- **AND** the company-profile explicit API local smoke artifact exists with decision `go`
- **AND** the explicit API smoke includes citations from the expected source
- **WHEN** the closure runs
- **THEN** the closure decision is `go`
- **AND** it records the provider base URL, source id, corpus trial summary, explicit API summary, citations, blockers, warnings, and recommended next action

#### Scenario: Closure blocks missing artifacts
- **GIVEN** either required input artifact is missing
- **WHEN** the closure runs
- **THEN** the closure decision is `blocked`
- **AND** it records a machine-readable missing-artifact reason code

#### Scenario: Closure reviews partial readiness
- **GIVEN** both required artifacts exist
- **AND** at least one required input is `review` or contains warnings without blockers
- **WHEN** the closure runs
- **THEN** the closure decision is `review`
- **AND** it records the warnings for manual follow-up

### Requirement: Business RAG user-loop closure preserves explicit invocation boundaries

The closure SHALL remain read-only and SHALL NOT alter runtime behavior.

#### Scenario: Closure validates side-effect boundaries
- **WHEN** the closure reads the explicit API smoke boundary
- **THEN** it requires default chat retrieval injection to remain disabled
- **AND** it requires chat invocation, model invocation, tool execution, source-binding creation, memory writes, audit writes, trace writes, and GraphRAG execution to remain not performed or not promoted

#### Scenario: Closure blocks boundary drift
- **GIVEN** the explicit API smoke boundary indicates default chat retrieval injection is enabled or a side effect was performed
- **WHEN** the closure runs
- **THEN** the closure decision is `blocked`
- **AND** it records a boundary drift reason code

### Requirement: Business RAG user-loop closure is refreshable from CLI

The system SHALL provide a local CLI exporter for refreshing the business RAG user-loop closure report.

#### Scenario: CLI exports reports
- **WHEN** the user runs the closure export script
- **THEN** JSON and Markdown reports are written under `docs/integration/business-rag-user-loop-closure/`
- **AND** the command exits non-zero only when the closure decision is `blocked`

