## ADDED Requirements

### Requirement: Production ownership gate MUST expose PostgreSQL advisory lock execution seam blockers

The worker ownership production gate MUST expose PostgreSQL advisory lock execution seam evidence inside the `vendor_lock_semantics` section when PostgreSQL advisory lock evidence is present or expected.

#### Scenario: Execution seam executor is missing

- **WHEN** the production ownership gate is inspected without an injected PostgreSQL advisory lock executor
- **THEN** the `vendor_lock_semantics` evidence MUST include execution seam contract version, status, executor binding, one-shot operation support, default enablement, production allowment, and missing sections
- **AND** the `vendor_lock_semantics` section MUST remain blocked
- **AND** production default worker ownership MUST remain disabled

#### Scenario: Opt-in execution does not bypass production enablement

- **WHEN** the PostgreSQL advisory lock execution seam can execute through an injected executor
- **THEN** the production ownership gate MUST still require adapter allowment, target decision readiness, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** SQL row lease/fencing MUST NOT be treated as PostgreSQL advisory lock authority

#### Scenario: Runtime gate coverage proves fail-closed execution posture

- **WHEN** runtime smoke and quality gates evaluate worker ownership store mode coverage
- **THEN** they MUST prove the default execution seam is blocked without executor
- **AND** they MUST prove opt-in acquire evidence can be produced only through the injected executor
- **AND** they MUST keep production gate and durable recovery gate blocked by worker ownership and rollout blockers
