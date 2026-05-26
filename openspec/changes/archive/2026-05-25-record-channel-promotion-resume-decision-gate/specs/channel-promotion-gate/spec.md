## ADDED Requirements

### Requirement: Promotion Record MUST Precede Implementation Resume

The system SHALL require a canonical promotion record before any channel resumes implementation for a deeper query read-model layer.

#### Scenario: Resume decision is recorded

- **WHEN** the team decides to resume implementation for a channel query capability
- **THEN** the promotion record MUST include channel, current layer, target layer, readiness evidence, blockers, decision, next allowed action, and explicit non-goals
- **AND** the target layer MUST be the shallowest eligible layer for that channel
- **AND** implementation MUST NOT include deeper query layers than the recorded target layer

#### Scenario: Missing record blocks implementation

- **WHEN** a channel implementation would add recent summary, query detail, query history, or query workspace behavior
- **AND** no canonical promotion record exists for that target layer
- **THEN** the next allowed action MUST be a spec, architecture, or readiness-check slice
- **AND** the implementation MUST NOT proceed by copying the `main_chat` product shell

### Requirement: Current Channel Promotion Decisions MUST Be Canonical

The system SHALL preserve the current promotion decisions for `main_chat`, `subagent_lane`, and `external_adapter` as canonical Phase I records.

#### Scenario: main_chat remains canonical baseline

- **WHEN** the team evaluates query workspace generalization
- **THEN** the promotion record MUST treat `main_chat` as the canonical `query_workspace` baseline
- **AND** further `main_chat` work MUST be justified as boundary clarification or explicit value, not default local expansion

#### Scenario: subagent_lane blocks deeper promotion by default

- **WHEN** the team evaluates `subagent_lane`
- **THEN** the promotion record MUST treat its current allowed layer as no deeper than its recorded dedicated detail capability
- **AND** query history or query workspace promotion MUST require a separate decision
- **AND** the non-goals MUST block copying `main_chat` history or workspace behavior into `subagent_lane`

#### Scenario: external_adapter remains spec-only until explicitly resumed

- **WHEN** the team evaluates `external_adapter`
- **THEN** the promotion record MUST treat it as a `recent summary` candidate with implementation paused by default
- **AND** the next allowed action MUST remain a recorded resume decision or readiness-check slice unless implementation is explicitly approved
- **AND** it MUST NOT advance to query detail, query history, or query workspace without first landing real recent summary evidence

### Requirement: Promotion Records MUST Preserve Shared Recent Summary Boundaries

The system SHALL preserve the current recent summary abstraction decision while keeping channel-specific builders.

#### Scenario: Shared fields are recorded without generic assembler

- **WHEN** a channel is evaluated for `recent summary`
- **THEN** the promotion record MUST identify the shared field set as `query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, and `recording_state`
- **AND** optional fields MAY include `latest_snapshot_id`, `last_success_stage`, and `last_warning_stage`
- **AND** the record MUST NOT require a generic recent summary assembler before a third real channel sample exists
