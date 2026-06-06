# domain-agent-grounded-answer-trial-surface Specification

## MODIFIED Requirements

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
