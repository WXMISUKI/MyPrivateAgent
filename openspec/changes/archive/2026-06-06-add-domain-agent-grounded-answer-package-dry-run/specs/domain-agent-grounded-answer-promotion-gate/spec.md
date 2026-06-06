# domain-agent-grounded-answer-promotion-gate Specification

## MODIFIED Requirements

### Requirement: Promotion gate returns a bounded trial decision

The system SHALL expose a machine-readable grounded-answer promotion decision for a domain agent.

#### Scenario: Domain agent is ready for grounded-answer trial
- **WHEN** provider readiness is ready
- **AND** grounding decision is allowed
- **AND** PromptOps evidence is active or review
- **AND** MemoryOps evidence keeps retrieved knowledge promotion explicit
- **AND** multi-turn eval evidence has passed
- **THEN** the promotion decision is `go`
- **AND** the recommended next action is to start a repo-side grounded-answer trial

#### Scenario: Package dry-run requires promotion go
- **WHEN** a grounded-answer package dry-run is requested
- **AND** the promotion decision is not `go`
- **THEN** the package dry-run MUST remain `review` or `blocked`
- **AND** promotion `go` alone still does not permit answer generation
