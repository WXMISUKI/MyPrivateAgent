## MODIFIED Requirements

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
