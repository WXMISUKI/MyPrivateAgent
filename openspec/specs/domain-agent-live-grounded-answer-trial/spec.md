# domain-agent-live-grounded-answer-trial Specification

## Purpose
TBD - created by archiving change add-domain-agent-live-grounded-answer-trial. Update Purpose after archive.
## Requirements
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

### Requirement: Company profile live trial is manifest-scoped
The system SHALL support an explicit company-profile domain agent live grounded-answer trial using the manifest-declared `company_profile_2025_trial` RAG source.

#### Scenario: Company profile agent retrieves from the declared source
- **GIVEN** the `company_profile` domain agent manifest declares `capabilities.rag_sources: [company_profile_2025_trial]`
- **AND** the configured provider returns `documents` and `metadata.evidence_pack.status=answerable`
- **WHEN** the live trial runs for domain `company.profile`
- **THEN** the provider retrieve request uses `knowledge_base_ids=["company_profile_2025_trial"]`
- **AND** the trial report status is `go`
- **AND** the output includes provider retrieve summary, package dry-run, and grounded-answer composition trial output

#### Scenario: Company profile live trial remains explicit
- **WHEN** the company-profile live trial runs
- **THEN** it does not call `/api/chat`
- **AND** it does not create source-to-agent binding, write memory, write audit or trace records, execute tools, call GraphRAG, mutate provider state, start OCR, promote retrieval defaults, or enable default chat retrieval injection

### Requirement: Explicit live grounded-answer API is callable
The system SHALL expose an explicit HTTP API for running a domain-agent live grounded-answer trial without changing default chat behavior.

#### Scenario: API returns a compact answerable response
- **GIVEN** a domain agent exists with manifest-declared `rag_sources`
- **AND** the provider returns answerable evidence
- **WHEN** a caller posts to `/api/domain-agents/{agent_id}/live-grounded-answer`
- **THEN** the response includes `ok=true`, status, reason code, answer preview, citations, retrieved document summaries, boundary, and nested full trial payload
- **AND** the response uses the selected domain agent manifest as the provider retrieval source scope

#### Scenario: API returns a compact blocked response
- **GIVEN** the provider is unreachable or returns an invalid retrieve response
- **WHEN** a caller posts to `/api/domain-agents/{agent_id}/live-grounded-answer`
- **THEN** the response includes `ok=false`, status `blocked`, a machine-readable reason code, blockers, boundary, and nested full trial payload

#### Scenario: API preserves explicit invocation boundaries
- **WHEN** the explicit live grounded-answer API runs
- **THEN** it does not call `/api/chat`
- **AND** it does not create source-to-agent binding, write memory, write audit or trace records, execute tools, call GraphRAG, mutate provider state, start OCR, promote retrieval defaults, or enable default chat retrieval injection

#### Scenario: API key is supplied
- **WHEN** a caller supplies a provider API key
- **THEN** the key may be used for provider HTTP calls
- **AND** the API response does not echo the secret value
