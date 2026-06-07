## MODIFIED Requirements

### Requirement: Explicit API local smoke can be exported
The system SHALL provide a local caller-side smoke exporter that verifies the explicit domain-agent live grounded-answer API against a running provider.

#### Scenario: Explicit API local smoke passes
- **GIVEN** the provider base URL is reachable
- **AND** the `company_profile` domain agent can retrieve answerable evidence from `company_profile_2025_trial`
- **WHEN** the local smoke calls `/api/domain-agents/company_profile/live-grounded-answer`
- **THEN** the smoke decision is `go`
- **AND** the report records answer preview, citations, document count, boundary, endpoint, provider URL, and recommended next action

#### Scenario: Explicit API local smoke is blocked
- **GIVEN** the provider is unreachable, the route fails, the response contract is invalid, or the safety boundary is missing
- **WHEN** the local smoke runs
- **THEN** the smoke decision is `blocked`
- **AND** it records a machine-readable reason code and recovery action

#### Scenario: Explicit API local smoke preserves boundaries
- **WHEN** the local smoke runs
- **THEN** it does not call `/api/chat`
- **AND** it does not create source-to-agent binding, write memory, write audit or trace records, execute tools, start provider services, call GraphRAG, mutate provider data, start OCR, promote retrieval defaults, or perform real LLM answer generation

#### Scenario: Provider API key is supplied
- **WHEN** the local smoke receives a provider API key
- **THEN** the key may be used for provider HTTP calls
- **AND** the smoke JSON and Markdown outputs do not include the secret value
