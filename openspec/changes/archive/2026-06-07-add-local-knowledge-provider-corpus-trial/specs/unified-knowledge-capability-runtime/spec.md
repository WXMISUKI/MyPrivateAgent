## MODIFIED Requirements

### Requirement: Local provider corpus trial is exportable
MyPrivateAgent SHALL provide a read-only local corpus trial for an approved provider-visible knowledge source.

#### Scenario: Local corpus trial passes
- **WHEN** the configured provider base URL is reachable
- **AND** the configured source is visible in `/api/rag/sources`
- **AND** its source document manifest is available
- **AND** answerable corpus questions return retrieved evidence and answer citations within the retrieve citation allowlist
- **AND** the negative-control query returns insufficient evidence without citations
- **THEN** the trial decision is `go`
- **AND** the output records source id, query cases, retrieve counts, answer statuses, citations, invalid citations, and recommended next action

#### Scenario: Local corpus trial needs review
- **WHEN** the provider is reachable but an answerable case returns weak or missing evidence
- **OR** the negative-control case returns unexpected evidence without violating citation allowlists
- **THEN** the trial decision is `review`
- **AND** the output identifies the case-level reason before any grounded-answer workflow uses the source

#### Scenario: Local corpus trial is blocked
- **WHEN** the provider is unreachable, the source is missing, the manifest fails, retrieve/answer calls fail, response contracts are invalid, or answer citations are outside the retrieve citation allowlist
- **THEN** the trial decision is `blocked`
- **AND** the output identifies the blocking check and recovery action

### Requirement: Local provider corpus trial preserves caller/provider boundaries
The local corpus trial SHALL remain explicit, read-only, and outside default chat grounding.

#### Scenario: Trial is run
- **WHEN** the local corpus trial exporter runs
- **THEN** it does not create source-to-agent binding, mutate domain-agent manifests, write audit or memory records, enable default `/api/chat` retrieval injection, run MyPrivateAgent orchestration, start provider services, promote retrieval backends, start OCR, or execute GraphRAG

#### Scenario: Provider API key is supplied
- **WHEN** the trial command receives a provider API key
- **THEN** it sends supported provider API headers to `/api/*` requests
- **AND** it never writes the secret value into JSON or Markdown output
