## ADDED Requirements

### Requirement: Production ownership gate MUST expose default enablement input source blockers

The worker ownership production gate MUST expose production default enablement input source evidence inside the `fail_closed_default_decision` section.

#### Scenario: Default enablement request lacks input source

- **WHEN** production default ownership enablement is requested without a ready input source
- **THEN** `fail_closed_default_decision` MUST remain blocked
- **AND** its evidence MUST include input source contract version, status, source kind, request id, requester, approval time, target store mode, rollout artifact, missing sections, and production default allowment
- **AND** production default worker ownership MUST remain disabled

#### Scenario: Input source does not bypass other gate sections

- **WHEN** the production default enablement input source is ready
- **THEN** the production gate MUST still require vendor lock semantics, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, durable ownership, stale fencing, migration readiness, and explicit default enablement
- **AND** SQL row lease/fencing MUST NOT be treated as default production authority

#### Scenario: Runtime gate coverage proves input source blocker

- **WHEN** runtime smoke and quality gates evaluate worker ownership store mode coverage
- **THEN** they MUST prove the default input source is blocked
- **AND** they MUST prove production default allowment remains false
