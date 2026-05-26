## ADDED Requirements
### Requirement: Sandbox Backend Must Support Dispatch Attempt Envelope Handoff
Sandbox worker backend evidence MUST describe the compact dispatch attempt envelope schema used by child executor dispatch handoff validation.

#### Scenario: Sandbox attempt envelope is valid
- **WHEN** an opt-in sandbox backend produces all required attempt fields
- **THEN** handoff validation MUST report the envelope as valid
- **AND** this validation MUST NOT start a worker or imply production dispatch enablement

#### Scenario: Sandbox attempt envelope is malformed
- **WHEN** required attempt fields are missing
- **THEN** handoff validation MUST fail closed with missing field evidence
