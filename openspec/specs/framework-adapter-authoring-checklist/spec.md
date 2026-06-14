# framework-adapter-authoring-checklist Specification

## Purpose

Define the side-effect-free authoring checklist and conservative promotion review contract for external framework adapters.

## Requirements

### Requirement: Framework adapter checklist is machine-readable
The system SHALL expose a side-effect-free framework adapter authoring checklist for a requested adapter candidate.

#### Scenario: Checklist is generated for a registered adapter
- **WHEN** a registered adapter id is reviewed
- **THEN** the checklist includes adapter identity, lifecycle mapping, readiness checks, governance timeline requirements, promotion gate, and non-goals
- **AND** the checklist includes `default_chat_entry = disabled`
- **AND** the checklist does not execute the adapter, call an external framework, mutate trace/audit state, or change `/api/chat`

#### Scenario: Checklist blocks unknown adapter
- **WHEN** an unknown adapter id is reviewed
- **THEN** the checklist status is `blocked`
- **AND** the result includes a machine-readable blocker for `adapter_not_registered`

### Requirement: Framework adapter promotion review is conservative
The system SHALL summarize whether an adapter candidate can proceed to a controlled pilot without promoting it into default main chat execution.

#### Scenario: Adapter precheck is ready
- **WHEN** adapter precheck evidence reports `ready = true`
- **THEN** the promotion review may report `pilot_candidate`
- **AND** `will_execute` remains `false`
- **AND** `default_chat_entry` remains `disabled`

#### Scenario: Adapter precheck is blocked
- **WHEN** adapter precheck evidence reports `ready = false`
- **THEN** the promotion review status is `blocked`
- **AND** the review includes missing packages, missing environment variables, or execution block reason when available

### Requirement: Checklist preserves adapter authoring boundaries
The framework adapter checklist SHALL NOT replace the Framework Adapter SPI, precheck, runtime pilot, external pilot, or Query Control mapping contracts.

#### Scenario: Checklist is consumed by a reviewer
- **WHEN** a reviewer inspects the checklist
- **THEN** the checklist points to required authoring sections
- **AND** it does not create a new adapter, register tools, invoke workers, modify provider bindings, or promote query detail/history/workspace layers
