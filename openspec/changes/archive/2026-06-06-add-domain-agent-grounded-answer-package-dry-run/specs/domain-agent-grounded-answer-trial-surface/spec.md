# domain-agent-grounded-answer-trial-surface Specification

## MODIFIED Requirements

### Requirement: Trial surface returns a bounded trial report

The system SHALL expose a machine-readable grounded-answer trial report for a requested domain agent.

#### Scenario: Trial is ready to proceed
- **WHEN** caller-supplied evidence lets grounding and promotion decisions return `allowed` and `go`
- **THEN** the trial report status is `go`
- **AND** the report includes grounding decision, promotion decision, citation allowlist, blockers, warnings, and recommended next action

#### Scenario: Package dry-run consumes trial report
- **WHEN** a grounded-answer package dry-run is requested
- **THEN** it may consume the trial report as its input
- **AND** consuming the trial report does not invoke provider, model, chat, or answer generation
