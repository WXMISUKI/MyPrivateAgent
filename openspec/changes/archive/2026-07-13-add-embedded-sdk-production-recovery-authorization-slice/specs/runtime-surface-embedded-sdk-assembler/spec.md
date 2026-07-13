## ADDED Requirements

### Requirement: Embedded SDK Runtime Surface assembly MUST expose authorization read models
The dedicated Embedded SDK Runtime Surface builder MUST expose production recovery authorization read models for default recovery posture and run-specific recovery views.

#### Scenario: Default recovery includes authorization summary
- **WHEN** Runtime Surface assembles `default_runtime_recovery`
- **THEN** the payload MUST include compact Embedded SDK production recovery authorization evidence
- **AND** the builder MUST preserve the existing recovery payload shape while adding the new authorization summary

#### Scenario: Run recovery includes authorization summary
- **WHEN** Runtime Surface assembles `run_recovery`
- **THEN** the payload MUST include compact Embedded SDK production recovery authorization evidence
- **AND** the authorization summary MUST remain separate from run-specific recoverability

#### Scenario: Builder remains read-model only
- **WHEN** Runtime Surface assembles authorization summaries
- **THEN** the builder MUST NOT execute recovery, claim ownership, submit approval, or start workers
- **AND** it MUST only project existing gate and readiness evidence into the read model
