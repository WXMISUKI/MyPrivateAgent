## ADDED Requirements

### Requirement: Local knowledge base user-loop package is exportable
MyPrivateAgent SHALL provide a read-only local knowledge base user-loop package for an approved provider-visible source.

#### Scenario: User-loop package emits go
- **WHEN** the corpus trial input confirms the configured source is visible and answerable cases have valid citations
- **AND** the explicit API smoke input confirms the domain-agent entry point returned citation-backed evidence for the same source
- **AND** no caller/provider boundary drift is detected
- **THEN** the package decision is `go`
- **AND** the output includes source id, provider base URL, endpoint, suggested questions, citation summary, input artifact paths, and recommended next action

#### Scenario: User-loop package emits review
- **WHEN** required source visibility and explicit API evidence are present
- **AND** at least one non-blocking upstream review warning is present
- **THEN** the package decision is `review`
- **AND** the output identifies the warning while preserving the local trial entry point and citations

#### Scenario: User-loop package emits blocked
- **WHEN** a required input artifact is missing, unreadable, mismatched to the requested source, lacks citations, reports blocked required checks, or shows boundary drift
- **THEN** the package decision is `blocked`
- **AND** the output identifies the blocking component and recovery action

### Requirement: Local knowledge base user-loop preserves runtime boundaries
The local knowledge base user-loop package SHALL remain explicit, read-only, and outside default chat grounding.

#### Scenario: Package is generated
- **WHEN** the package exporter runs
- **THEN** it does not call the provider, start services, mutate domain-agent manifests, create source-to-agent bindings, write audit or memory records, enable default `/api/chat` retrieval injection, invoke a model, run orchestration, start OCR, or execute GraphRAG

#### Scenario: Boundary drift is detected
- **WHEN** an input artifact reports default chat retrieval injection, model invocation, tool execution, source binding creation, memory write, audit write, trace write, runtime mutation, or GraphRAG promotion
- **THEN** the package decision is `blocked`
- **AND** the boundary field identifies the drifted value

### Requirement: Local knowledge base user-loop is tester friendly
The local knowledge base user-loop package SHALL expose enough usage guidance for a local developer or tester to try the approved knowledge source without reading provider internals.

#### Scenario: Suggested questions are emitted
- **WHEN** the package is generated
- **THEN** it includes a concise list of suggested business questions for the configured source
- **AND** each suggested question includes an expected mode of either `answerable` or `insufficient_evidence`

#### Scenario: Explicit entry point is emitted
- **WHEN** explicit API smoke evidence is available
- **THEN** the package includes the endpoint, agent id, domain, query, answer preview, and citations consumed from that evidence
