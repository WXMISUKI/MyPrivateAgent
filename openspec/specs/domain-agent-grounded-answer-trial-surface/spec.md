# domain-agent-grounded-answer-trial-surface Specification

## Purpose

Define the explicit opt-in trial surface that lets callers inspect whether a domain agent can enter a grounded-answer repo-side trial. This capability does not enable default `/api/chat` retrieval injection.

## Requirements

### Requirement: Trial surface returns a bounded trial report

The system SHALL expose a machine-readable grounded-answer trial report for a requested domain agent.

#### Scenario: Trial is ready to proceed
- **WHEN** caller-supplied evidence lets grounding and promotion decisions return `allowed` and `go`
- **THEN** the trial report status is `go`
- **AND** the report includes grounding decision, promotion decision, citation allowlist, blockers, warnings, and recommended next action

#### Scenario: Composition trial remains downstream
- **WHEN** a grounded-answer composition trial exists
- **THEN** trial surface remains an upstream readiness layer
- **AND** the trial report alone does not generate an answer preview without package/composition evaluation

#### Scenario: Trial requires review
- **WHEN** grounding or promotion decision returns `review` and no blocker exists
- **THEN** the trial report status is `review`
- **AND** the report includes warnings that identify the review reason

#### Scenario: Trial is blocked
- **WHEN** grounding or promotion decision returns `blocked`
- **THEN** the trial report status is `blocked`
- **AND** the report includes machine-readable blockers

#### Scenario: Package dry-run consumes trial report
- **WHEN** a grounded-answer package dry-run is requested
- **THEN** it may consume the trial report as its input
- **AND** consuming the trial report does not invoke provider, model, chat, or answer generation

### Requirement: Trial surface is explicit opt-in

The grounded-answer trial surface SHALL be reachable only through an explicit trial entrypoint and SHALL NOT alter default chat behavior.

#### Scenario: Caller invokes trial endpoint
- **WHEN** a caller invokes the grounded-answer trial endpoint for an agent
- **THEN** the endpoint returns a trial report
- **AND** it does not call `/api/chat`
- **AND** it does not enable default retrieval injection

### Requirement: Trial surface is side-effect-free

The trial surface SHALL only evaluate supplied evidence and existing read-only contracts.

#### Scenario: Trial is evaluated
- **WHEN** a trial report is generated
- **THEN** no provider request is sent
- **AND** no answer is generated
- **AND** no source binding, memory, audit, trace, or chat state is mutated

### Requirement: Trial surface preserves graph boundary

The trial surface SHALL NOT treat document RAG evidence as GraphRAG execution readiness.

#### Scenario: Graph trial is requested before promotion
- **WHEN** a trial request sets graph usage
- **THEN** the trial report status is `blocked`
- **AND** the report identifies GraphRAG execution as not promoted
