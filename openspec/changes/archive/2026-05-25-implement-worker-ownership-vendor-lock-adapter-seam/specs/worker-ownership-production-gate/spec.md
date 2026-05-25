## ADDED Requirements

### Requirement: Production ownership gate MUST expose vendor lock adapter seam blockers
The worker ownership production gate MUST expose vendor lock adapter seam evidence inside the `vendor_lock_semantics` section.

#### Scenario: Vendor lock adapter seam is missing
- **WHEN** the production ownership gate is inspected without a vendor lock adapter seam
- **THEN** the `vendor_lock_semantics` section evidence MUST include adapter seam contract version, status, adapter kind, target backend, scope, capability flags, production allowment, SQL-row-lease-not-vendor-lock evidence, and missing sections
- **AND** the `vendor_lock_semantics` section MUST remain blocked
- **AND** production default ownership enforcement MUST remain disabled

#### Scenario: Adapter seam does not bypass production enablement
- **WHEN** the vendor lock adapter seam is ready
- **THEN** production default ownership MUST still require target decision readiness, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** SQL row lease/fencing MUST NOT be treated as vendor-specific distributed lock authority
