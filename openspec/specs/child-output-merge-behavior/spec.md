# child-output-merge-behavior Specification

## Purpose
Define how child executor output is merged into parent-facing state based on intent and section semantics.
## Requirements
### Requirement: Child Executor Output Must Declare Stable Intent And Merge Behavior

Child executor output records MUST expose both a stable `intent_label` and a stable merge behavior description so parent merge logic does not depend on ad hoc payload inspection.

#### Scenario: Replay record describes merge semantics

- **GIVEN** a child executor output is executed and merged
- **WHEN** the parent replays child executor outputs
- **THEN** each replay record MUST expose `intent_label`
- **AND** it MUST expose the merge behavior applied to that record

### Requirement: Parent Merge Must Use Intent-Aware Minimal Merge Modes

Parent merge MUST use a bounded set of merge modes instead of ad hoc per-field branching.

#### Scenario: Risk review output merges into parent semantics

- **GIVEN** a child output with intent `risk_review`
- **WHEN** parent merge runs
- **THEN** entities, focus points, and action items MUST follow the configured intent-aware merge modes
- **AND** the merged result MUST be visible through parent metadata and compact summary

### Requirement: Replay, Summary, And Parent Metadata Must Stay Coherent

Replay, compact summary, and parent metadata MUST describe compatible merge semantics rather than three divergent views.

#### Scenario: Summary reads merged semantics

- **GIVEN** one or more child outputs were merged into a parent
- **WHEN** `summarize_child_executor_outputs(...)` is called
- **THEN** the summary MUST expose the latest merged semantics view
- **AND** that view MUST be explainable from replay records and parent metadata
