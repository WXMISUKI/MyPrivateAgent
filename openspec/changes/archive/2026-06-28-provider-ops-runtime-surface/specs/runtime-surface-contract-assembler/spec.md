# runtime-surface-contract-assembler Specification

## ADDED Requirements

### Requirement: Runtime Surface MAY expose provider ops posture as a compact contract
The Runtime Surface profile SHALL be able to expose provider ops posture as a compact governance-visible contract.

#### Scenario: Runtime profile includes provider ops
- **WHEN** a caller requests the runtime profile
- **THEN** the profile MAY include a `provider_ops` section
- **AND** the section contains compact summary counts and provider posture entries
- **AND** it remains read-only

#### Scenario: Missing provider ops does not break the profile
- **WHEN** provider ops evidence is unavailable
- **THEN** Runtime Surface returns a stable profile shape
- **AND** the provider ops section falls back to an empty or degraded state
- **AND** other runtime profile sections remain available

#### Scenario: Provider ops does not add mutations
- **WHEN** Runtime Surface consumers inspect provider ops posture
- **THEN** they do not gain configuration writes, provider invoke actions, routing controls, or promotion controls through that section
