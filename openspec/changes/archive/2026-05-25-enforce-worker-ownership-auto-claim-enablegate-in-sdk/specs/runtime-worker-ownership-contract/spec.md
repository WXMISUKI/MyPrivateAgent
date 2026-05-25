# runtime-worker-ownership-contract Delta

## ADDED Requirements

### Requirement: SDK MUST support opt-in auto-claim enablement gate enforcement

The Embedded SDK MUST provide an explicit opt-in mode that evaluates the worker ownership auto-claim enablement gate before calling `claim_run`.

#### Scenario: Default SDK behavior remains descriptor-evidence-only

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** auto-claim is not enabled
- **THEN** SDK MUST NOT call `claim_run`
- **AND** recovery behavior MUST remain compatible with descriptor-evidence-only mode

#### Scenario: Legacy opt-in auto-claim remains compatible

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** `worker_ownership_auto_claim_enabled = true`
- **AND** gate enforcement is not enabled
- **THEN** SDK MAY call `claim_run` through the existing opt-in seam

#### Scenario: Gate-enforced auto-claim blocks claim_run when gate is blocked

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** auto-claim and gate enforcement are enabled
- **AND** the explicit auto-claim enablement gate is blocked
- **THEN** SDK MUST NOT call `claim_run`
- **AND** SDK MUST return fail-closed worker ownership evidence
- **AND** the evidence MUST include the nested enablement gate status and blocked reason

#### Scenario: Gate-enforced auto-claim allows claim_run when gate is ready

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** auto-claim and gate enforcement are enabled
- **AND** the explicit auto-claim enablement gate is ready
- **THEN** SDK MAY call `claim_run`
- **AND** it MUST still record compact ownership evidence only
