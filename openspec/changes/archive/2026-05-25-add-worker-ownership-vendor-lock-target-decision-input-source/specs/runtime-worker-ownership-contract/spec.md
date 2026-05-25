## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose vendor lock target decision input source evidence

The runtime worker ownership contract MUST expose a read-only input source for vendor lock target decisions so operators can distinguish undecided lock targets from recorded operational decisions.

#### Scenario: Default input source is blocked

- **WHEN** the runtime worker ownership contract is inspected without vendor lock target decision input source evidence
- **THEN** `worker_ownership.vendor_lock_semantics.policy.target_decision.input_source.overall_status` MUST be `blocked`
- **AND** missing decision source fields MUST be machine-readable
- **AND** SQL row lease/fencing MUST NOT be treated as vendor lock input evidence

#### Scenario: Target decision embeds input source evidence

- **WHEN** `worker_ownership.vendor_lock_semantics.policy.target_decision` is inspected
- **THEN** it MUST include `input_source`
- **AND** a blocked input source MUST keep the target decision blocked
- **AND** it MUST NOT create or start a vendor lock adapter

#### Scenario: Ready input source remains descriptive

- **WHEN** an approved config, operations decision record, rollout artifact, or manual approval input source is complete
- **THEN** the input source MAY report `overall_status = ready`
- **AND** it MUST remain descriptive evidence only
- **AND** it MUST NOT enable production default worker ownership
