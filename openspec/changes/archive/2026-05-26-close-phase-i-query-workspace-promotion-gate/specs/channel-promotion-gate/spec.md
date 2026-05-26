## ADDED Requirements

### Requirement: Phase I Channel Promotion State MUST Be Closed

The channel promotion gate SHALL treat the current Phase I channel promotion map as closed until a future promotion decision explicitly reopens a deeper layer.

#### Scenario: Phase I closure records channel states

- **WHEN** the team reviews Phase I query channel promotion
- **THEN** `main_chat` MUST remain the canonical `query_workspace` baseline
- **AND** `subagent_lane` MUST remain no deeper than `query_detail`
- **AND** `external_adapter` MUST remain no deeper than `recent_summary`

#### Scenario: Closed state blocks deeper channel work

- **WHEN** a future change proposes `subagent_lane` query history or workspace behavior
- **OR** a future change proposes `external_adapter` query detail, history, or workspace behavior
- **THEN** that change MUST include a new promotion decision
- **AND** implementation MUST NOT proceed under the Phase I closure record alone

### Requirement: Phase I Reopen Rule MUST Be Explicit

The system SHALL require a dedicated reopen rule before Phase I channel promotion work resumes.

#### Scenario: Reopen decision allows future implementation

- **WHEN** the team decides to reopen channel promotion implementation
- **THEN** the new promotion decision MUST identify the channel, current layer, target layer, readiness evidence, blockers, next allowed action, and explicit non-goals
- **AND** the target layer MUST be exactly one layer deeper than the current approved layer unless a separate spec explains why the layer order is changing

#### Scenario: Reopen decision is absent

- **WHEN** no reopen decision exists
- **THEN** the next default project slice MUST NOT add deeper channel query capability
- **AND** the team SHOULD continue with Phase II runtime-core implementation or delivery-surface slimming work instead
