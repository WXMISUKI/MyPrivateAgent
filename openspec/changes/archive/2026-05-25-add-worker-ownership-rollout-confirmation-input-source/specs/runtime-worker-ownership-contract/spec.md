## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose rollout confirmation input source evidence
The runtime worker ownership contract MUST expose a read-only input source for production rollout confirmation decisions so operators can distinguish missing rollout evidence from a recorded operational decision.

#### Scenario: Rollout confirmation input source defaults to blocked
- **WHEN** the rollout confirmation input source contract is built without source metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing sections for source kind, decision id, approval, target store mode, rollback plan reference, fallback policy reference, renewal lifecycle reference, and auto-claim decision reference
- **AND** it MUST NOT confirm production rollout or enable production default worker ownership

#### Scenario: Rollout confirmation decision embeds input source
- **WHEN** the rollout confirmation decision contract is built
- **THEN** it MUST include an `input_source` object
- **AND** a blocked input source MUST keep the decision blocked
- **AND** the decision MUST NOT execute rollout, enable recovery auto-claim, or start background workers

#### Scenario: Complete rollout confirmation input source becomes ready
- **WHEN** a config, operations decision record, deployment artifact, change ticket, or manual approval source includes decision id, approver, approval time, strict SQL target store mode, rollback plan reference, fallback policy reference, renewal lifecycle reference, and auto-claim decision reference
- **THEN** the input source MAY report `overall_status = ready`
- **AND** it MUST still not enable production default worker ownership by itself
