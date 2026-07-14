## ADDED Requirements

### Requirement: LangGraph smoke evidence is projectable as governance read model
The system SHALL convert LangGraph controlled pilot smoke reports into side-effect-free runtime-plane governance projection evidence.

#### Scenario: Passed smoke projection is built
- **WHEN** a passed LangGraph controlled pilot smoke report is projected
- **THEN** the projection uses `runtime_plane_governance_projection`
- **AND** it includes adapter id, runtime, result status, trace reference, event count, stage counts, and read-model boundaries
- **AND** it includes trace-backed evidence for smoke status, acceptance, snapshot availability, and query-control recording availability

#### Scenario: Blocked smoke projection is built
- **WHEN** a blocked LangGraph controlled pilot smoke report is projected
- **THEN** the projection result status is `blocked`
- **AND** trace-backed evidence reports `external_call_attempted = false`
- **AND** no trace, audit, approval, scheduler, checkpoint, worker, or chat state is written

#### Scenario: Failed smoke projection preserves error summary
- **WHEN** a failed LangGraph controlled pilot smoke report includes external error evidence
- **THEN** the projection includes compact error type and detail
- **AND** the projection remains read-only and does not promote LangGraph to production runtime
