## MODIFIED Requirements

### Requirement: Resolved approval submissions MUST be immutable

The system MUST treat resolved approvals as immutable lifecycle objects.

#### Scenario: Repeat the same resolved decision
- **WHEN** an already approved approval receives another approved submission
- **THEN** the system MUST return `approval_replayed`
- **AND** it MUST NOT re-execute a consumed continuation
- **AND** optional governance trace recording MUST NOT change the replay result

#### Scenario: Attempt to reverse a resolved decision
- **WHEN** an already denied approval receives an approved submission
- **THEN** the system MUST return `approval_ignored`
- **AND** it MUST NOT change the approval status
- **AND** optional governance trace recording MUST NOT change the ignored result

