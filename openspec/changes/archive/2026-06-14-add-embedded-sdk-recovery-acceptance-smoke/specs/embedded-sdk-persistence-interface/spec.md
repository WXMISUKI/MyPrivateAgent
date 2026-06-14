## ADDED Requirements

### Requirement: Persistence posture MUST gate recovery acceptance

The Embedded SDK recovery acceptance smoke MUST use persistence posture as a gate for explicit durable recovery consumption.

#### Scenario: Durable ready posture can pass acceptance with registry evidence

- **WHEN** the workspace backend reports durable ready posture
- **AND** required continuation registry bindings are present
- **THEN** the acceptance smoke MAY report `decision = accepted`
- **AND** it MUST still describe production auto-recovery as gated

#### Scenario: Memory preview posture blocks durable acceptance

- **WHEN** the workspace backend reports memory preview posture
- **THEN** the acceptance smoke MUST report `decision = blocked`
- **AND** it MUST keep any in-process recovery evidence separate from durable cross-process recovery acceptance
