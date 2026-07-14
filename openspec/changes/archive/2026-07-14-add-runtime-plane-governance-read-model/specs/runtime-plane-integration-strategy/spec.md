## MODIFIED Requirements

### Requirement: Each stage must include a review loop
The system MUST require a written review after each runtime-plane stage so the team can verify that implementation still matches the plan.

#### Scenario: Stage is completed
- **WHEN** a runtime-plane stage completes
- **THEN** the team MUST record whether the implementation stayed within scope
- **AND** the review MUST state whether the next stage is still justified

#### Scenario: Stage drifts out of scope
- **WHEN** a runtime-plane stage starts to grow into a wider platform effort
- **THEN** the team MUST pause and return to the freeze-and-align stage
- **AND** the next task MUST be to tighten the adapter boundary or the stage definition

#### Scenario: Post-Stage-1 governance read model is added
- **WHEN** Stage 1 adapter envelopes are projected for governance visibility
- **THEN** the projection MUST remain side-effect-free and read-only
- **AND** the review MUST state that trace persistence, approval submission, Runtime Surface API wiring, and default chat changes are still out of scope
