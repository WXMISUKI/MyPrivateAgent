## ADDED Requirements

### Requirement: Provider readiness evidence has a stop condition
The provider capability roadmap SHALL define a stop condition for handoff and readiness evidence slices so provider readiness work does not continue indefinitely.

#### Scenario: Caller-side trial passes
- **WHEN** a caller-side trial outcome passes required provider access checks
- **THEN** the roadmap SHALL allow the readiness evidence chain to close with a go/review/blocked decision
- **AND** subsequent work SHALL move to the next focused control contract instead of adding more readiness evidence by default

#### Scenario: Default chat behavior is requested
- **WHEN** maintainers want default chat retrieval injection after readiness closure
- **THEN** the roadmap SHALL route that work through grounding policy and evaluation gates
- **AND** it SHALL NOT be treated as a readiness evidence follow-up
