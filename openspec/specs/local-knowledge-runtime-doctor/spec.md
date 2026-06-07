# local-knowledge-runtime-doctor Specification

## Purpose

Provide a local developer-facing doctor contract for checking whether MyPrivateAgent can use the explicit local knowledge runtime path without changing default chat behavior.

## Requirements

### Requirement: Local knowledge runtime doctor is available
The system SHALL provide a local doctor mode that checks whether the explicit local knowledge runtime path is usable.

#### Scenario: Knowledge runtime doctor passes
- **GIVEN** the external knowledge provider is reachable
- **AND** the `company_profile` explicit API smoke returns `decision=go`
- **WHEN** a developer runs the knowledge runtime doctor
- **THEN** the report decision is `go`
- **AND** the report status is `ok`
- **AND** it includes endpoint, provider URL, agent id, domain, query, check results, boundary, and recommended next action

#### Scenario: Knowledge runtime doctor is blocked
- **GIVEN** the provider is unreachable, the explicit API route fails, the response contract is invalid, or required evidence is missing
- **WHEN** the knowledge runtime doctor runs
- **THEN** the report decision is `blocked`
- **AND** the report status is `fail`
- **AND** it includes a machine-readable reason code, blockers, and a concrete recovery action

#### Scenario: Knowledge runtime doctor requires review
- **GIVEN** the explicit API smoke returns `decision=review`
- **WHEN** the knowledge runtime doctor runs
- **THEN** the report decision is `review`
- **AND** the report status is `warn`
- **AND** it includes warnings and a next action that does not promote default chat retrieval

### Requirement: Local knowledge runtime doctor preserves boundaries
The knowledge runtime doctor SHALL remain an explicit, read-only local diagnostic.

#### Scenario: Doctor runs
- **WHEN** the knowledge runtime doctor runs
- **THEN** it does not call `/api/chat`
- **AND** it does not start provider services, create source-to-agent binding, write memory, write audit or trace records, execute tools, mutate provider data, run OCR, execute GraphRAG, promote retrieval defaults, or perform real LLM answer generation

#### Scenario: Provider API key is supplied
- **WHEN** the knowledge runtime doctor receives a provider API key
- **THEN** the key may be used for provider HTTP calls
- **AND** the doctor output does not include the secret value

### Requirement: Local knowledge runtime doctor is exposed through existing doctor surfaces
The system SHALL expose the knowledge runtime doctor through the existing doctor CLI and may expose it through the existing doctor API.

#### Scenario: CLI doctor runs
- **WHEN** a developer runs `python backend/scripts/doctor.py --knowledge-runtime`
- **THEN** the CLI prints compact JSON
- **AND** exits with `0` for `go`, `2` for `review`, and `1` for `blocked`

#### Scenario: API doctor runs
- **WHEN** a caller requests `/api/doctor?knowledge_runtime=true`
- **THEN** the API returns the same read-only report shape
- **AND** it does not require a frontend UI change
