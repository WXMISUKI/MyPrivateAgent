## ADDED Requirements

### Requirement: Reviewer and fallback MUST compose with model step evidence

The existing reviewer and fallback execution-loop contracts MUST compose with model-step evidence without creating a separate execution path.

#### Scenario: Reviewer consumes model step evidence

- **WHEN** a run executes with `model_step` and reviewer
- **THEN** the reviewer MUST be able to read compact model-step evidence from run metadata
- **AND** reviewer approval or rejection MUST keep existing event and fail-closed semantics

#### Scenario: Model step failure uses existing fallback events

- **WHEN** model-step execution raises
- **THEN** fallback handling MUST use existing `execution_loop_fallback_applied` or `execution_loop_failed` events
- **AND** no provider-specific failure event is required in this slice
