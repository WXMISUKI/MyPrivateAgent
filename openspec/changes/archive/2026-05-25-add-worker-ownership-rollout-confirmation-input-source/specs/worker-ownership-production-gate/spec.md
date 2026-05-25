## ADDED Requirements

### Requirement: Production ownership gate MUST expose rollout confirmation input source blockers
The worker ownership production gate MUST expose rollout confirmation input source evidence inside the `rollout_checklist` section.

#### Scenario: Rollout checklist carries input source blocker
- **WHEN** the worker ownership production gate is inspected without rollout confirmation input source evidence
- **THEN** the `rollout_checklist` section evidence MUST include rollout confirmation input source contract version, status, source kind, decision id, approver, approval time, target store mode, references, and missing sections
- **AND** the `rollout_checklist` section MUST remain blocked
- **AND** production default ownership enforcement MUST remain disabled

#### Scenario: Rollout input source does not bypass production gate
- **WHEN** the rollout confirmation input source is ready
- **THEN** production default ownership MUST still require vendor lock semantics, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** SQL row lease/fencing MUST NOT be treated as rollout confirmation authority
