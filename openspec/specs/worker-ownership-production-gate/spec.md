# worker-ownership-production-gate Specification

## Purpose

Define the fail-closed production gate that must pass before worker ownership can become default execution authority for recovery, retry, or worker dispatch.
## Requirements
### Requirement: Worker ownership production gate MUST be machine-readable

The runtime MUST expose a production gate before worker ownership can become default execution authority for recovery, retry, or worker dispatch.

The gate MUST include:

- contract version
- overall status
- production default enabled flag
- readiness sections
- missing sections
- next allowed action
- non-goals

#### Scenario: Production gate is blocked

- **WHEN** vendor lock semantics, renewal supervision, rollout, migration, auto-claim policy, or audit evidence is missing
- **THEN** the gate reports `overall_status = blocked`
- **AND** worker ownership remains explicit or opt-in
- **AND** default production ownership enforcement remains disabled

#### Scenario: Production gate is ready

- **WHEN** all production readiness sections are complete
- **THEN** the gate may report `overall_status = ready`
- **AND** enabling default production ownership still requires explicit runtime configuration

### Requirement: Production ownership MUST require explicit default enablement strategy

The production gate MUST keep default worker ownership execution authority fail-closed until every required production section is ready and an explicit runtime configuration requests default enablement.

#### Scenario: Default enablement strategy is blocked

- **WHEN** vendor lock semantics, renewal supervision, rollout readiness, recovery-entry auto-claim policy, stale fencing fail-closed evidence, audit evidence, or durable ownership store readiness is incomplete
- **THEN** the `fail_closed_default_decision` section remains not ready
- **AND** its evidence MUST list the blocking sections
- **AND** `production_default_allowed` MUST be false

#### Scenario: All required sections are ready but default enablement is not requested

- **WHEN** every required production ownership section is ready
- **AND** explicit production default enablement was not requested
- **THEN** the `fail_closed_default_decision` section remains not ready
- **AND** production default ownership enforcement remains disabled

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

### Requirement: Production ownership MUST distinguish SQL row lease from vendor lock

The production gate MUST NOT treat SQL row lease/fencing as a vendor-specific distributed lock unless vendor lock semantics are explicitly present.

#### Scenario: SQL row lease only

- **WHEN** the runtime uses SQLAlchemy row lease/fencing without vendor-specific lock semantics
- **THEN** the production gate remains blocked
- **AND** the gate identifies `vendor_lock_semantics` as a missing section
- **AND** the `vendor_lock_semantics` section evidence MUST identify missing lock adapter, lock scope, fencing guarantee, failover semantics, TTL/renewal semantics, stale owner cleanup, and production allowment sections

#### Scenario: Vendor lock contract is present but not production-allowed

- **WHEN** the vendor lock semantics contract is ready but reports `production_lock_allowed = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** production default ownership enforcement remains disabled

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

### Requirement: Production ownership gate MUST expose PostgreSQL vendor lock probe blockers

The worker ownership production gate MUST expose PostgreSQL advisory lock probe evidence inside the `vendor_lock_semantics` section when a PostgreSQL vendor lock adapter seam is present or expected.

#### Scenario: PostgreSQL probe is missing

- **WHEN** the production ownership gate is inspected without PostgreSQL advisory lock probe readiness
- **THEN** the `vendor_lock_semantics` section evidence MUST include PostgreSQL probe contract version, status, advisory lock family, lock key derivation, lock scope, fencing binding, TTL/renewal strategy, failover behavior, stale cleanup, probe safety, execution flag, SQL-row-lease-not-vendor-lock evidence, and missing sections
- **AND** the `vendor_lock_semantics` section MUST remain blocked
- **AND** production default ownership enforcement MUST remain disabled

#### Scenario: PostgreSQL probe does not bypass production enablement

- **WHEN** the PostgreSQL advisory lock probe is ready
- **THEN** production default ownership MUST still require adapter capability readiness, target decision readiness, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** SQL row lease/fencing MUST NOT be treated as PostgreSQL advisory lock authority

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

### Requirement: Production ownership MUST require renewal and rollout evidence

Default production worker ownership MUST require heartbeat renewal supervision and rollout readiness evidence.

#### Scenario: Renewal supervisor is missing

- **WHEN** no renewal supervisor contract is present
- **THEN** the gate remains blocked
- **AND** it MUST NOT allow default recovery ownership enforcement
- **AND** the `heartbeat_renewal_supervisor` section evidence MUST identify missing renewal supervisor readiness sections

#### Scenario: Renewal supervisor contract is present but not production-enabled

- **WHEN** the renewal supervisor contract is present but reports `supervisor_enabled_by_default = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `heartbeat_renewal_supervisor` section remains not ready
- **AND** production default ownership enforcement remains disabled

#### Scenario: Renewal supervisor seam exists without background supervision

- **WHEN** the renewal supervisor contract reports `renew_once_supported = true`
- **AND** no background supervisor is present or enabled by default
- **THEN** the `heartbeat_renewal_supervisor` section remains blocked
- **AND** the evidence MUST expose that explicit one-shot renewal does not imply production background supervision

#### Scenario: Controlled lifecycle exists without default start

- **WHEN** the renewal supervisor contract reports `controlled_lifecycle_supported = true`
- **AND** it reports `starts_by_default = false`
- **THEN** the `heartbeat_renewal_supervisor` section remains blocked
- **AND** the evidence MUST expose lifecycle status, latest renewal status, stop support, and fail-closed posture
- **AND** production default ownership enforcement remains disabled

#### Scenario: Rollout checklist is incomplete

- **WHEN** migration, stale fencing, recovery-entry auto-claim, audit rollout checks, fallback policy, strict-mode rollout confirmation, or rollback planning are incomplete
- **THEN** the gate remains blocked
- **AND** missing checklist entries are machine-readable
- **AND** the `rollout_checklist` section evidence MUST identify missing rollout readiness sections

#### Scenario: Rollout operationalization is incomplete

- **WHEN** the rollout operationalization contract is missing rollback plan, fallback policy, renewal lifecycle verification, auto-claim decision, or explicit rollout confirmation
- **THEN** the worker ownership production gate remains blocked
- **AND** the `rollout_checklist` section evidence MUST expose the missing rollout artifacts
- **AND** production default ownership enforcement remains disabled

#### Scenario: Rollout checklist carries decision blocker

- **WHEN** the worker ownership production gate is built
- **THEN** the `rollout_checklist` section evidence MUST include `rollout_confirmation_decision_contract_version`
- **AND** it MUST include `rollout_confirmation_decision_status`
- **AND** it MUST include `rollout_decision_recorded`
- **AND** it MUST include `rollout_target_store_mode`
- **AND** it MUST include `rollout_confirmation_missing_sections`
- **AND** the section MUST remain blocked when the decision record is blocked

#### Scenario: Decision record does not bypass vendor lock or production enablement

- **WHEN** the rollout confirmation decision record is ready
- **THEN** the worker ownership production gate MUST still require vendor lock semantics, renewal supervisor readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** strict SQL row lease/fencing MUST NOT be treated as vendor-specific distributed lock semantics

#### Scenario: Rollout contract is present but not production-confirmed

- **WHEN** the rollout readiness contract is present but reports `production_rollout_confirmed = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `rollout_checklist` section remains not ready
- **AND** production default ownership enforcement remains disabled

### Requirement: Production ownership MUST keep recovery entry auto-claim explicit

Recovery entry auto-claim MUST remain disabled by default until the production gate is ready and an explicit runtime configuration enables it.

#### Scenario: Auto-claim policy is missing

- **WHEN** no recovery-entry auto-claim policy contract is present
- **THEN** the worker ownership production gate remains blocked
- **AND** the `recovery_entry_auto_claim_policy` section evidence MUST identify missing auto-claim policy sections
- **AND** default recovery entry auto-claim remains disabled

#### Scenario: Auto-claim policy is present but not default-enabled

- **WHEN** the auto-claim policy contract is present but reports `auto_claim_enabled_by_default = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `recovery_entry_auto_claim_policy` section remains not ready
- **AND** default recovery entry auto-claim remains disabled

#### Scenario: Auto-claim is requested while gate is blocked

- **WHEN** recovery entry auto-claim would run under a blocked production gate
- **THEN** the runtime MUST fail closed or keep descriptor-evidence-only mode
- **AND** it MUST NOT silently claim ownership as a side effect

#### Scenario: Production gate exposes auto-claim entrypoint allowlist posture

- **WHEN** the worker ownership production gate is built
- **THEN** the `recovery_entry_auto_claim_policy` section evidence MUST include `auto_claim_entrypoint_allowlist_contract_version`
- **AND** it MUST include `auto_claim_entrypoint_allowlist_status`
- **AND** it MUST include `auto_claim_allowed_entrypoints`
- **AND** it MUST include `auto_claim_missing_entrypoints`
- **AND** it MUST include `auto_claim_default_auto_claim_enabled`
- **AND** it MUST include `auto_claim_requires_production_gate_ready`
- **AND** the section MUST remain blocked when auto-claim is not enabled by default

#### Scenario: Production gate exposes explicit auto-claim enablement blocker

- **WHEN** the worker ownership production gate is built
- **THEN** the `recovery_entry_auto_claim_policy` section evidence MUST include `auto_claim_enablement_gate_contract_version`
- **AND** it MUST include `auto_claim_enablement_gate_status`
- **AND** it MUST include `auto_claim_will_auto_claim`
- **AND** it MUST include `auto_claim_enablement_missing_sections`
- **AND** it MUST include `auto_claim_enablement_blocked_reason`
- **AND** the section MUST remain blocked when the enablement gate is blocked

#### Scenario: SDK gate enforcement does not enable production default ownership

- **WHEN** SDK gate-enforced auto-claim is configured
- **THEN** worker ownership production gate MUST remain the production authorization boundary
- **AND** default production ownership MUST remain disabled unless the production gate and explicit default enablement strategy are ready
- **AND** gate-enforced SDK auto-claim MUST NOT be treated as rollout confirmation

### Requirement: Production ownership MUST keep audit evidence descriptive

Ownership audit evidence MUST remain a descriptive readiness signal and MUST NOT become a production execution authorization source.

#### Scenario: Audit evidence is missing

- **WHEN** no ownership audit evidence contract is present
- **THEN** the worker ownership production gate remains blocked
- **AND** the `ownership_audit_evidence` section evidence MUST identify missing audit evidence sections

#### Scenario: Audit evidence is present but incomplete

- **WHEN** audit evidence is compact but operation history, recovery operation link, timeline writer, or idempotent dedupe evidence is missing
- **THEN** the worker ownership production gate remains blocked
- **AND** the `ownership_audit_evidence` section remains not ready

#### Scenario: Audit evidence is treated as authorization

- **WHEN** an audit evidence contract reports `authorization_source = true`
- **THEN** the worker ownership production gate MUST remain blocked
- **AND** production ownership MUST NOT be default-enabled from audit evidence alone

### Requirement: Production ownership gate MUST expose vendor lock target decision blockers

The worker ownership production gate MUST expose vendor lock target decision evidence inside the `vendor_lock_semantics` section so operators can distinguish an undecided lock target from a missing implementation.

#### Scenario: Vendor lock target decision is missing

- **WHEN** the production ownership gate is inspected without a vendor lock target decision
- **THEN** the `vendor_lock_semantics` section MUST remain blocked
- **AND** its evidence MUST include `vendor_lock_target_decision_status = blocked`
- **AND** its evidence MUST include missing target decision sections
- **AND** its evidence MUST include `vendor_lock_target_sql_row_lease_is_vendor_lock = false`
- **AND** its evidence MUST include `vendor_lock_target_production_allowed = false`

#### Scenario: SQL row lease remains separate from vendor lock target decision

- **WHEN** strict SQL row lease/fencing is available
- **THEN** the production ownership gate MUST still report SQL row lease as not being a vendor lock target
- **AND** default production ownership MUST remain disabled unless all production gate sections are ready and explicit default enablement is requested

### Requirement: Production ownership gate MUST expose vendor lock target decision input source blockers

The worker ownership production gate MUST expose vendor lock target decision input source evidence inside the `vendor_lock_semantics` section.

#### Scenario: Target decision input source is missing

- **WHEN** the production ownership gate is inspected without target decision input source evidence
- **THEN** the `vendor_lock_semantics` section MUST remain blocked
- **AND** its evidence MUST include `vendor_lock_target_input_source_status = blocked`
- **AND** its evidence MUST include input source missing sections
- **AND** its evidence MUST include `vendor_lock_target_input_sql_row_lease_is_vendor_lock = false`

#### Scenario: Input source does not bypass production enablement

- **WHEN** a target decision input source is ready
- **THEN** production default ownership MUST still require vendor lock semantics, rollout, renewal supervisor, auto-claim policy, audit evidence, and explicit production default enablement

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
### Requirement: Production ownership gates MUST cover PostgreSQL rollout artifact consumer evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL rollout artifact consumer evidence exists, is fail-closed by default, and does not bypass production default enablement gates.

#### Scenario: Runtime smoke covers default consumer blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL rollout artifact consumer contract version, default status, default missing sections, default non-execution, and default non-enablement fields
- **AND** the production gate MUST remain blocked

#### Scenario: Runtime smoke covers complete artifact bridge

- **WHEN** runtime smoke builds a complete PostgreSQL rollout artifact consumer with a ready opt-in execution seam contract
- **THEN** it MUST prove the consumer can produce ready nested input source evidence
- **AND** it MUST prove that the consumer still reports `will_enable_production_default = false`
- **AND** production default worker ownership MUST remain disabled

#### Scenario: SQL row lease is not promoted by artifact consumer

- **WHEN** strict SQL row lease/fencing is present
- **THEN** PostgreSQL rollout artifact consumer evidence MUST NOT mark SQL row lease/fencing as vendor lock authority
- **AND** production gate and durable recovery gate MUST remain blocked until explicit production enablement and rollout decisions are complete

### Requirement: Production ownership gates MUST cover PostgreSQL target artifact binding evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL target artifact binding evidence exists, is fail-closed by default, and does not bypass production lock or default ownership gates.

#### Scenario: Runtime smoke covers default binding blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL target artifact binding contract version, default status, default missing sections, default non-execution, and default non-enablement fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers complete target decision bridge

- **WHEN** runtime smoke builds a complete PostgreSQL target artifact binding from the same rollout artifact family
- **THEN** it MUST prove nested target decision input and target decision evidence are ready
- **AND** it MUST prove the binding does not execute advisory lock SQL
- **AND** it MUST prove the binding does not enable production lock by itself

#### Scenario: Target binding does not bypass production recovery blocker

- **WHEN** PostgreSQL target artifact binding evidence is ready
- **THEN** durable recovery production gate MUST remain blocked until worker ownership production gate and rollout enablement are explicitly ready

### Requirement: Production ownership gates MUST cover PostgreSQL vendor lock semantics binding evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL vendor lock semantics binding evidence exists, is fail-closed by default, and does not update production gate readiness by itself.

#### Scenario: Runtime smoke covers default semantics binding blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL semantics binding contract version, default status, default missing sections, default non-execution, default non-production-gate-update, and default non-enablement fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers ready semantics candidate

- **WHEN** runtime smoke builds a complete PostgreSQL semantics binding from ready target binding and ready opt-in execution seam evidence
- **THEN** it MUST prove nested PostgreSQL probe, adapter, and vendor lock semantics evidence are ready
- **AND** it MUST prove the binding does not execute advisory lock SQL
- **AND** it MUST prove the binding does not enable production lock or update production gate readiness by itself

#### Scenario: Semantics candidate does not bypass durable recovery blocker

- **WHEN** PostgreSQL vendor lock semantics binding evidence is ready
- **THEN** durable recovery production gate MUST remain blocked until worker ownership production gate and rollout enablement are explicitly ready

### Requirement: Production ownership gates MUST cover PostgreSQL production gate wiring decision evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL vendor lock production gate wiring decision evidence exists, is fail-closed by default, and does not update the default production gate by itself.

#### Scenario: Runtime smoke covers default wiring decision blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL wiring decision contract version, default status, default missing sections, default non-update, default non-enablement, and default non-execution fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers approved wiring decision

- **WHEN** runtime smoke builds a complete wiring decision from ready semantics binding evidence
- **THEN** it MUST prove the decision can become ready and `wiring_allowed = true`
- **AND** it MUST prove the decision does not update the production gate or enable production lock

#### Scenario: Wiring decision does not bypass durable recovery blocker

- **WHEN** PostgreSQL vendor lock production gate wiring decision evidence is ready
- **THEN** durable recovery production gate MUST remain blocked until worker ownership production gate and rollout enablement are explicitly ready

### Requirement: Production ownership gates MUST cover production gate composition dry-run evidence

Worker ownership production gate quality coverage MUST prove that composition dry-run evidence exists, is fail-closed by default, and remains non-executing even when all required input evidence is ready.

#### Scenario: Runtime smoke covers default dry-run blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include composition dry-run contract version, default status, missing sections, blocking reasons, and default non-execution fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers complete dry-run evidence

- **WHEN** runtime smoke builds complete ready evidence for all required dry-run inputs
- **THEN** it MUST prove the dry-run can report ready and `production_default_would_be_allowed = true`
- **AND** it MUST prove the dry-run does not enable production defaults, execute locks, start background workers, or run recovery auto-claim

#### Scenario: Dry-run remains separate from production enablement

- **WHEN** dry-run evidence is ready
- **THEN** Quality Gate and Runtime Contract Gate MUST continue to treat default production ownership and durable recovery production recovery as blocked unless explicit production enablement is separately implemented

### Requirement: Production ownership gates MUST cover production enablement runtime config consumer evidence

Worker ownership production gate quality coverage MUST prove that production enablement runtime config consumer evidence exists, is fail-closed by default, and remains non-executing even when complete config evidence is supplied.

#### Scenario: Runtime smoke covers default runtime config consumer blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include production enablement runtime config consumer contract version, default status, default missing sections, and default non-execution fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers complete runtime config consumer evidence

- **WHEN** runtime smoke builds complete caller-owned production enablement config and ready nested dry-run evidence
- **THEN** it MUST prove the consumer can report ready
- **AND** it MUST prove nested enablement input source and composition dry-run evidence are ready
- **AND** it MUST prove the consumer does not enable production defaults, execute locks, start background workers, or run recovery auto-claim

#### Scenario: Runtime config consumer remains separate from production enablement

- **WHEN** runtime config consumer evidence is ready
- **THEN** Quality Gate and Runtime Contract Gate MUST continue to treat default production ownership and durable recovery production recovery as blocked unless explicit production enablement is separately implemented

### Requirement: Production ownership gates MUST cover runtime factory config binding evidence

Worker ownership production gate quality coverage MUST prove that the Runtime Surface / embedded runtime factory binding for production enablement runtime config exists, remains fail-closed by default, and remains non-authorizing when complete config evidence is supplied.

#### Scenario: Runtime smoke covers default factory binding blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include production enablement runtime config factory binding status
- **AND** it MUST prove the default binding is blocked without config
- **AND** it MUST prove default binding evidence does not enable production defaults, execute locks, start background workers, or run recovery auto-claim

#### Scenario: Runtime smoke covers complete factory binding evidence

- **WHEN** runtime smoke builds an embedded runtime factory with complete caller-owned production enablement config
- **THEN** it MUST prove the factory-built worker ownership contract exposes ready runtime config consumer evidence
- **AND** it MUST prove nested enablement input source and composition dry-run evidence are ready
- **AND** it MUST prove the binding does not enable production defaults, execute locks, start background workers, or run recovery auto-claim

#### Scenario: Quality summary distinguishes binding evidence from authorization

- **WHEN** Quality Gate and Runtime Contract Gate summarize worker ownership production enablement config coverage
- **THEN** the summary MUST expose whether factory binding evidence is covered
- **AND** missing or old artifacts MUST fail closed
- **AND** covered binding evidence MUST NOT be treated as production ownership authorization
