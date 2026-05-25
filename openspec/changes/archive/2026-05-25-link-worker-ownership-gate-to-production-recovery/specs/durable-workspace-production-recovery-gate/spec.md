## MODIFIED Requirements

### Requirement: Durable workspace production recovery gate MUST be machine-readable

The runtime MUST expose a production recovery gate before cross-process recovery can become default runtime behavior.

The gate MUST include:

- contract version
- overall status
- production default enabled flag
- readiness sections
- missing sections
- next allowed action
- non-goals

#### Scenario: Worker ownership gate evidence is linked

- **WHEN** the durable recovery gate evaluates worker ownership readiness
- **THEN** the `worker_ownership_production_gate` section MUST include nested worker ownership gate evidence
- **AND** the evidence MUST include ownership gate contract version, overall status, production-default flag, missing sections, and next allowed action
- **AND** the durable recovery gate MUST remain blocked when the ownership gate is blocked or not production-default enabled
