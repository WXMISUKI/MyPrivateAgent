# domain-agent-grounded-answer-composition-trial Specification

## Purpose

Define the deterministic grounded-answer composition trial that builds a controlled answer preview from a ready package without invoking providers, models, or default chat behavior.

## Requirements

### Requirement: Composition trial returns a bounded answer preview

The system SHALL expose a deterministic grounded-answer composition trial for a requested domain agent.

#### Scenario: Package is ready
- **WHEN** the grounded-answer package status is `ready`
- **THEN** the composition status is `ready`
- **AND** the result includes an answer preview, used citations, composition policy, fallback behavior, blockers, and warnings

#### Scenario: Package needs review
- **WHEN** the grounded-answer package status is `review`
- **THEN** the composition status is `review`
- **AND** no answer preview is generated

#### Scenario: Package is blocked
- **WHEN** the grounded-answer package status is `blocked`
- **THEN** the composition status is `blocked`
- **AND** no answer preview is generated

### Requirement: Composition trial is side-effect-free

The composition trial SHALL remain an explicit opt-in preview and SHALL NOT alter runtime behavior.

#### Scenario: Composition trial runs
- **WHEN** a caller invokes the composition trial endpoint
- **THEN** no provider, model, or `/api/chat` request is sent
- **AND** no memory, audit, trace, or source binding state is mutated

### Requirement: Composition trial preserves citation and graph boundaries

The composition trial SHALL only use citations from the package allowlist and SHALL keep GraphRAG blocked when not promoted.

#### Scenario: Citation set is constrained
- **WHEN** the package allowlist contains citations
- **THEN** the composition preview may only use citations from that allowlist

#### Scenario: Graph blocker remains active
- **WHEN** the package is blocked by GraphRAG not being promoted
- **THEN** the composition status remains `blocked`
- **AND** the graph blocker is preserved
