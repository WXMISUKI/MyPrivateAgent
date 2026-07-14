# langgraph-controlled-pilot-smoke Specification

## Purpose

Define the explicit LangGraph controlled pilot smoke contract that is gated by readiness and summarized as acceptance evidence.

## Requirements

### Requirement: LangGraph controlled pilot smoke is readiness-gated
The system SHALL expose an explicit LangGraph controlled pilot smoke contract that evaluates readiness before attempting external pilot execution.

#### Scenario: Readiness blocks smoke before external call
- **WHEN** LangGraph controlled pilot readiness is blocked
- **THEN** the smoke report status is `blocked`
- **AND** `external_call_attempted` is `false`
- **AND** blockers from readiness are included
- **AND** default chat and production promotion remain disabled

#### Scenario: Ready smoke executes explicit external pilot
- **WHEN** LangGraph controlled pilot readiness is ready
- **THEN** the smoke calls the existing external pilot execution path
- **AND** the smoke report includes pilot status, final output availability, event count, snapshot availability, query-control recording availability, and acceptance checks
- **AND** default chat and production promotion remain disabled

#### Scenario: External pilot failure is captured as smoke evidence
- **WHEN** readiness is ready but external pilot execution returns failed status
- **THEN** the smoke report status is `failed`
- **AND** the report includes external error type and detail when available
- **AND** the report remains controlled pilot evidence rather than production promotion
