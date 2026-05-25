## MODIFIED Requirements

### Requirement: Production recovery MUST preserve loader non-execution boundary

DurableRecoveryLoader MUST remain a read-only candidate loader unless an explicit production recovery handoff policy is ready.

#### Scenario: Handoff policy is defined

- **WHEN** loader execution handoff policy is implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `loader_execution_handoff_policy` as ready
- **AND** the gate still remains blocked when worker ownership, audit, rollout, registry policy, or checkpoint/cursor gate sections are missing

#### Scenario: Loader candidate is ready but executor binding is missing

- **WHEN** DurableRecoveryLoader can produce a registry-backed candidate
- **AND** no recovery executor binding exists
- **THEN** the handoff decision remains blocked
- **AND** the loader MUST NOT execute recovery by itself
