## MODIFIED Requirements

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate is consumed by durable recovery

- **WHEN** durable recovery production gating consumes `worker_ownership.production_gate`
- **THEN** the ownership gate MUST remain descriptive evidence only
- **AND** SQL row lease/fencing MUST NOT be treated as production recovery authorization
- **AND** production ownership enforcement MUST remain disabled unless the ownership gate is ready and explicitly enabled
