## ADDED Requirements

### Requirement: Production registry/checkpoint policy MUST be machine-readable

The runtime MUST expose compact production policy evidence for registry binding resolution and checkpoint/resume cursor gating before durable cross-process recovery can become default behavior.

The policy contract MUST include:

- contract version
- readiness flag
- registry binding policy evidence
- checkpoint/resume cursor policy evidence
- authorization source flag
- required evidence
- non-goals

#### Scenario: Policy readiness is available

- **WHEN** registry-backed reattach policy and checkpoint/resume cursor gate policy are available
- **THEN** policy readiness reports `ready = true`
- **AND** `authorization_source = false`

#### Scenario: Policy evidence is missing

- **WHEN** registry binding policy or checkpoint/resume cursor policy evidence is missing
- **THEN** production recovery gate includes the corresponding missing section
- **AND** default production recovery execution remains disabled

### Requirement: Registry/checkpoint policy MUST NOT execute recovery

Registry/checkpoint policy readiness MUST remain side-effect-free governance evidence.

#### Scenario: Policy is ready but rollout is missing

- **WHEN** registry/checkpoint policy readiness is ready
- **AND** rollout or worker ownership production gate is missing
- **THEN** production recovery remains blocked
- **AND** policy readiness MUST NOT be treated as executor authorization

### Requirement: Runtime quality gates MUST cover registry/checkpoint policy

Runtime contract smoke, Quality Gate summary, Runtime Contract Gate, and snapshot guard MUST expose registry/checkpoint production policy coverage.

#### Scenario: Smoke proves policy readiness

- **WHEN** runtime contract smoke runs
- **THEN** it includes registry/checkpoint production policy evidence
- **AND** quality gates expose `production_recovery_registry_checkpoint_policy_coverage.policy_smoke`
