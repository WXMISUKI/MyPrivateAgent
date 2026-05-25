## MODIFIED Requirements

### Requirement: Production ownership MUST require renewal and rollout evidence

Default production worker ownership MUST require heartbeat renewal supervision and rollout readiness evidence.

#### Scenario: Rollout operationalization is incomplete

- **WHEN** the rollout operationalization contract is missing rollback plan, fallback policy, renewal lifecycle verification, auto-claim decision, or explicit rollout confirmation
- **THEN** the worker ownership production gate remains blocked
- **AND** the `rollout_checklist` section evidence MUST expose the missing rollout artifacts
- **AND** production default ownership enforcement remains disabled
