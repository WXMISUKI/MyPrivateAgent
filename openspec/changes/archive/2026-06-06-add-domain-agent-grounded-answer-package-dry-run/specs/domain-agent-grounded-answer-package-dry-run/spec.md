# domain-agent-grounded-answer-package-dry-run Specification

## ADDED Requirements

### Requirement: Package dry-run returns a bounded answer package

The system SHALL expose a deterministic grounded-answer package dry-run for a requested domain agent.

#### Scenario: Trial is ready
- **WHEN** the grounded-answer trial status is `go`
- **THEN** the package status is `ready`
- **AND** the package includes citations, prompt binding, memory boundary, fallback policy, blockers, warnings, and reason code

#### Scenario: Trial needs review
- **WHEN** the grounded-answer trial status is `review`
- **THEN** the package status is `review`
- **AND** the package preserves trial warnings

#### Scenario: Trial is blocked
- **WHEN** the grounded-answer trial status is `blocked`
- **THEN** the package status is `blocked`
- **AND** the package preserves trial blockers

### Requirement: Package dry-run is side-effect-free

The package dry-run SHALL only build an input package for a future answer path.

#### Scenario: Package is built
- **WHEN** a caller requests the package dry-run
- **THEN** no model is invoked
- **AND** no answer is generated
- **AND** no provider, chat, memory, audit, trace, or source binding state is mutated

### Requirement: Package dry-run preserves graph boundary

The package dry-run SHALL NOT promote GraphRAG execution.

#### Scenario: Graph request remains blocked
- **WHEN** the input trial is blocked by GraphRAG not being promoted
- **THEN** the package status remains `blocked`
- **AND** the package preserves the graph blocker
