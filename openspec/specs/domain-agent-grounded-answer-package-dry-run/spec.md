# domain-agent-grounded-answer-package-dry-run Specification

## Purpose

Define the deterministic dry-run package that prepares a future grounded-answer input bundle without invoking providers, models, or default chat behavior.

## Requirements

### Requirement: Package dry-run returns a bounded answer package

The system SHALL expose a deterministic grounded-answer package dry-run for a requested domain agent.

#### Scenario: Trial is ready
- **WHEN** the grounded-answer trial status is `go`
- **THEN** the package status is `ready`
- **AND** the package includes citations, prompt binding, memory boundary, fallback policy, blockers, warnings, and reason code

#### Scenario: Composition trial consumes package
- **WHEN** a grounded-answer composition trial is requested
- **THEN** it may consume the ready package as its input
- **AND** consuming the package does not invoke provider, model, or chat behavior

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

### Requirement: Package dry-run preserves provider readiness
The grounded-answer package dry-run SHALL preserve compact provider readiness evidence from the input trial report when that evidence is present.

#### Scenario: Ready trial carries provider readiness into package
- **WHEN** the grounded-answer trial status is `go`
- **AND** the trial report includes `provider_readiness.status = ready`
- **THEN** the package status is `ready`
- **AND** the package includes the same compact provider readiness summary
- **AND** the package does not call the provider, chat, model, tools, memory, audit, trace, or source binding

#### Scenario: Review trial preserves provider warning
- **WHEN** the grounded-answer trial status is `review`
- **AND** the trial report includes provider readiness warnings such as source catalog degradation
- **THEN** the package status is `review`
- **AND** the package preserves provider readiness warnings

#### Scenario: Blocked trial preserves provider blocker
- **WHEN** the grounded-answer trial status is `blocked`
- **AND** the trial report includes provider readiness blockers such as provider unreachable
- **THEN** the package status is `blocked`
- **AND** the package preserves machine-readable provider blockers

#### Scenario: Graph boundary remains blocked
- **WHEN** the grounded-answer trial status is `blocked`
- **AND** the trial report includes `provider_readiness.graph_query_status = gated`
- **THEN** the package status is `blocked`
- **AND** the package preserves the GraphRAG promotion boundary
- **AND** document RAG readiness is not treated as GraphRAG execution readiness
