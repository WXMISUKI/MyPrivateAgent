# embedded-sdk-execution-loop-reviewer-fallback Specification

## Purpose

Define stable reviewer and fallback event payload contracts for the Embedded SDK execution loop.

## Requirements

### Requirement: Embedded SDK declares reviewer event payloads
The Embedded SDK contract SHALL declare stable event status kinds and required payloads for execution-loop reviewer outcomes.

#### Scenario: Reviewer approves a run
- **WHEN** an Embedded SDK execution loop emits `execution_loop_reviewed`
- **THEN** the SDK event contract includes that status kind
- **AND** required payload includes `review` and `loop_step`

#### Scenario: Reviewer rejects a run
- **WHEN** an Embedded SDK execution loop emits `execution_loop_review_rejected`
- **THEN** the SDK event contract includes that status kind
- **AND** required payload includes `review` and `loop_step`
- **AND** the run fails closed with a machine-readable review reason

### Requirement: Embedded SDK declares fallback event payloads
The Embedded SDK contract SHALL declare stable event status kinds and required payloads for execution-loop fallback outcomes.

#### Scenario: Fallback handles reviewer failure
- **WHEN** a reviewer callable raises and fallback handles the error
- **THEN** the execution loop emits `execution_loop_fallback_applied`
- **AND** the SDK event contract requires `fallback`, `error`, and `loop_step`
- **AND** the run may continue without changing default chat behavior

#### Scenario: Fallback fails closed
- **WHEN** a reviewer callable raises and fallback does not handle the error
- **THEN** the execution loop emits `execution_loop_failed`
- **AND** the SDK event contract requires `fallback`, `error`, and `loop_step`
- **AND** the run fails closed with `stop_reason = loop_exception`

### Requirement: Reviewer and fallback hardening preserves runtime boundaries
The reviewer/fallback contract SHALL NOT introduce real model calls, default chat routing, new framework adapters, or provider invocations.

#### Scenario: SDK contract is inspected
- **WHEN** a consumer reads the Embedded SDK contract
- **THEN** reviewer/fallback status kinds are visible as governance evidence
- **AND** no new provider, chat, worker, framework, or model execution is implied
