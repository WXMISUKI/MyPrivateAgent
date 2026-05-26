## ADDED Requirements

### Requirement: Phase I Exit Line MUST Prefer Boundary Closure Over Channel Parity

The query workspace generalization phase SHALL close when promotion boundaries are stable, even if non-`main_chat` channels have not reached full workspace parity.

#### Scenario: Phase I exits without channel parity

- **WHEN** `main_chat` is the canonical workspace baseline
- **AND** `subagent_lane` and `external_adapter` each have explicit blocked deeper layers
- **AND** recent summary abstraction has a recorded current decision
- **THEN** Phase I MAY be closed
- **AND** the team MUST NOT require every channel to reach query workspace before moving to Phase II

#### Scenario: Phase II becomes default next phase

- **WHEN** Phase I is closed
- **THEN** the default next project planning frame MUST move to Phase II runtime-core implementation and delivery-surface slimming
- **AND** new channel workspace implementation MUST require a future promotion decision change
