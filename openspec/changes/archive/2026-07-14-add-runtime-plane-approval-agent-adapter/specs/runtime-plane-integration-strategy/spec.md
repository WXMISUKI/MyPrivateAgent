## MODIFIED Requirements

### Requirement: Runtime plane development must be stage-gated
The system MUST use stage-gated runtime development so that each stage has a bounded scope, a review point, and a stop condition.

#### Scenario: Stage 0 freeze
- **WHEN** the project enters the freeze-and-align stage
- **THEN** the team MUST stop expanding local harness/runtime helpers into a production execution platform
- **AND** the docs MUST record the stage stop condition

#### Scenario: Stage 1 runtime slice
- **WHEN** the first runtime-plane slice is implemented
- **THEN** it MUST be a minimal adapter-backed slice
- **AND** it MUST not expand into a full platform rewrite

#### Scenario: Stage 1 approval-agent slice
- **WHEN** the approval-agent slice is implemented
- **THEN** it MUST normalize high-risk tool intent into an approval-pending envelope
- **AND** it MUST not execute the high-risk tool, submit production approval, resume execution, or change default chat behavior
