# runtime-worker-ownership-contract Specification

## Purpose

Define worker ownership, lease, heartbeat, and fencing evidence for runtime recovery or continuation operations that may run outside the original process.
## Requirements
### Requirement: Runtime MUST expose worker ownership as a first-class contract

The runtime MUST define a machine-readable worker ownership contract for any recovery or continuation operation that may run outside the original process. The default embedded runtime factory MUST expose the configured ownership adapter as a runtime dependency boundary.

#### Scenario: Ownership contract is declared

- **WHEN** a consumer inspects runtime recovery capabilities
- **THEN** the runtime MUST expose whether worker ownership is implemented
- **AND** it MUST expose the ownership contract version
- **AND** it MUST distinguish ownership readiness from durable storage readiness
- **AND** it MUST expose whether the default worker ownership adapter is durable
- **AND** it MUST identify that SDK enforcement remains opt-in on descriptor ownership evidence

#### Scenario: Runtime factory creates SDK with ownership dependency

- **WHEN** `EmbeddedRuntimeFactory.create_sdk()` is called without overriding ownership dependencies
- **THEN** the SDK MUST receive the factory's configured worker ownership store
- **AND** recovery gate behavior MUST remain descriptor-evidence driven

### Requirement: Runtime MUST support a durable worker ownership adapter

The runtime MUST provide an opt-in durable worker ownership adapter that preserves the same lease, heartbeat, validation, and fencing semantics as the in-memory adapter while storing ownership evidence in SQL-backed state.

#### Scenario: Durable adapter declares SQL ownership capability

- **WHEN** a durable worker ownership store is inspected through its contract
- **THEN** it MUST report `adapter_kind = "sqlalchemy"`
- **AND** it MUST report `durable = true`
- **AND** it MUST expose `claim_run`, `heartbeat`, `validate_ownership`, and `get_lease`

#### Scenario: Durable claim survives a new store instance

- **GIVEN** a SQL-backed worker ownership store has claimed a run
- **WHEN** another store instance uses the same database session factory
- **THEN** it MUST read the same lease through `get_lease`
- **AND** it MUST block a competing worker while the lease is unexpired

#### Scenario: Durable expired lease replacement increments fencing

- **GIVEN** a SQL-backed worker ownership lease has expired
- **WHEN** another worker claims the same run
- **THEN** the new lease MUST replace the expired ownership
- **AND** the new lease MUST use a greater `fencing_token`

#### Scenario: Durable heartbeat preserves fencing

- **GIVEN** a SQL-backed worker owns an unexpired lease
- **WHEN** the worker sends a heartbeat with the current `worker_id` and `lease_id`
- **THEN** the lease expiration MUST be refreshed
- **AND** the `fencing_token` MUST remain unchanged

#### Scenario: Durable stale fencing fails closed

- **WHEN** a worker validates SQL-backed ownership with a stale `fencing_token`
- **THEN** validation MUST return `owned = false`
- **AND** the reason MUST be `stale_worker_fencing_token`
- **AND** the recovery entrypoint MUST NOT treat the evidence as executable authorization

### Requirement: Runtime MUST configure default worker ownership store mode

The runtime MUST expose a configurable default worker ownership store mode while keeping the default behavior compatible with the existing in-memory ownership adapter.

#### Scenario: Default ownership store remains memory-only

- **WHEN** no `WORKER_OWNERSHIP_STORE_MODE` is configured
- **THEN** default embedded runtime dependencies MUST use the in-memory worker ownership store
- **AND** the runtime contract MUST report `worker_ownership.adapter_kind = "in_memory"`
- **AND** it MUST report `worker_ownership.durable = false`

#### Scenario: SQL ownership store can be selected explicitly

- **WHEN** `WORKER_OWNERSHIP_STORE_MODE` is configured as `strict_sql`
- **THEN** default embedded runtime dependencies MUST use the SQLAlchemy worker ownership store
- **AND** the runtime contract MUST report `worker_ownership.adapter_kind = "sqlalchemy"`
- **AND** it MUST report `worker_ownership.durable = true`

#### Scenario: SQL ownership bootstrap failure fails closed in strict mode

- **WHEN** `WORKER_OWNERSHIP_STORE_MODE` is configured as `strict_sql`
- **AND** the SQL ownership store cannot initialize
- **THEN** default dependency construction MUST fail closed
- **AND** it MUST NOT silently return an in-memory ownership store

#### Scenario: SQL ownership bootstrap failure can fallback in prefer mode

- **WHEN** `WORKER_OWNERSHIP_STORE_MODE` is configured as `prefer_sql_with_fallback`
- **AND** the SQL ownership store cannot initialize
- **THEN** default dependency construction MAY return an in-memory ownership store
- **AND** the runtime contract MUST still expose the configured ownership mode for diagnosis

#### Scenario: Runtime contract exposes ownership store mode source

- **WHEN** a consumer inspects the embedded runtime factory contract
- **THEN** `default_runtime_profile` MUST include `worker_ownership_store_mode`
- **AND** it MUST include `worker_ownership_store_mode_source`
- **AND** `configurable_bootstrap_knobs` MUST include `WORKER_OWNERSHIP_STORE_MODE`

### Requirement: Worker ownership MUST use lease and fencing evidence

The runtime MUST use explicit lease and fencing evidence before a worker can claim recovery execution ownership. The first implementation MAY provide an in-memory adapter seam, but it MUST keep the same claim, heartbeat, validation, and fencing semantics expected from future durable adapters.

#### Scenario: Worker claims ownership

- **WHEN** a worker attempts to claim a run for recovery
- **THEN** it MUST create or refresh a lease record
- **AND** the lease MUST include `run_id`, `worker_id`, `lease_id`, `fencing_token`, `lease_expires_at`, and `claimed_at`
- **AND** the claim MUST fail closed if an unexpired lease with a newer or equal fencing token exists

#### Scenario: Worker heartbeat refreshes ownership

- **GIVEN** a worker owns a lease
- **WHEN** it sends a heartbeat before expiration
- **THEN** the lease expiration MAY be extended
- **AND** the fencing token MUST remain stable for the same lease
- **AND** the heartbeat MUST NOT create a parallel owner

#### Scenario: Worker validates ownership

- **GIVEN** a worker owns an unexpired lease
- **WHEN** it validates ownership with the current `worker_id`, `lease_id`, and `fencing_token`
- **THEN** validation MUST return owned evidence
- **AND** the validation evidence MUST remain compact and non-executable

#### Scenario: Expired ownership is replaced

- **GIVEN** a worker lease has expired
- **WHEN** another worker claims the same run
- **THEN** the new claim MAY replace the expired lease
- **AND** the new lease MUST use a greater `fencing_token`

### Requirement: Runtime MUST gate worker ownership store mode coverage

The runtime contract quality gate MUST emit and summarize machine-readable evidence that the default worker ownership store mode remains conservative, configurable, and observable.

#### Scenario: Runtime smoke covers ownership store mode

- **WHEN** runtime contract smoke runs
- **THEN** it MUST emit a `worker_ownership_store_mode` check
- **AND** the check MUST prove the default mode is `memory_only`
- **AND** the check MUST prove the default ownership adapter is in-memory and non-durable
- **AND** the check MUST prove `WORKER_OWNERSHIP_STORE_MODE` is listed in configurable bootstrap knobs

#### Scenario: Quality gate summarizes ownership store mode coverage

- **WHEN** a quality gate report includes the `worker_ownership_store_mode` check
- **THEN** `runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke` MUST be true only when the check evidence is complete
- **AND** the summary MUST include the observed default mode, adapter kind, durability, strict mode status, and fallback mode status

#### Scenario: Missing ownership store mode coverage fails closed

- **WHEN** Runtime Contract Gate reads an old or dirty artifact without worker ownership store mode coverage
- **THEN** `runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke` MUST be false
- **AND** Runtime Contract Snapshot MUST report degradation if the coverage object or `mode_smoke` field is missing

### Requirement: Recovery operation MUST include ownership evidence when implemented

Recovery operation evidence MUST include ownership fields once worker ownership is implemented.

#### Scenario: Recovery operation runs under a worker lease

- **GIVEN** worker ownership is implemented
- **AND** a worker has claimed a recovery lease
- **WHEN** the worker records a recovery operation
- **THEN** the operation evidence MUST include `worker_ownership.implemented = true`
- **AND** it MUST include `worker_id`, `lease_id`, `fencing_token`, and `lease_status`
- **AND** it MUST remain compact and non-executable

### Requirement: Ownership loss MUST fail closed

The runtime MUST stop or block recovery continuation when worker ownership is lost. The SDK MAY enforce this as an opt-in gate when a worker ownership store and ownership evidence are explicitly supplied.

#### Scenario: Lease expires before recovery completes

- **WHEN** a worker tries to continue recovery after its lease expires
- **THEN** the runtime MUST block the continuation
- **AND** it MUST record `operation_status = blocked`
- **AND** the recovery reason MUST be `worker_ownership_lost`

#### Scenario: Fencing token is stale

- **WHEN** a worker presents a stale fencing token
- **THEN** the runtime MUST reject the recovery operation
- **AND** it MUST record `operation_status = blocked`
- **AND** the recovery reason MUST be `stale_worker_fencing_token`
- **AND** the recovery entrypoint MUST NOT execute the recovered continuation

#### Scenario: Valid ownership allows recovery

- **GIVEN** worker ownership is implemented
- **AND** the worker presents valid lease and fencing evidence
- **WHEN** the recovery entrypoint records a recovery operation
- **THEN** the operation evidence MUST include validated `worker_ownership`
- **AND** the recovery entrypoint MAY continue execution

#### Scenario: Ownership store is not configured

- **WHEN** SDK recovery runs without an ownership store
- **THEN** existing recovery behavior MUST remain compatible
- **AND** operation evidence MUST continue to report `worker_ownership.implemented = false`

### Requirement: SDK MUST support opt-in auto-claim enablement gate enforcement

The Embedded SDK MUST provide an explicit opt-in mode that evaluates the worker ownership explicit auto-claim enablement gate before calling `claim_run`.

#### Scenario: Default SDK behavior remains descriptor-evidence-only

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** worker ownership auto-claim is not enabled
- **THEN** SDK MUST NOT call `claim_run`
- **AND** recovery behavior MUST remain compatible with descriptor-evidence-only mode

#### Scenario: Legacy opt-in auto-claim remains compatible

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** `worker_ownership_auto_claim_enabled = true`
- **AND** gate enforcement is not enabled
- **THEN** SDK MAY call `claim_run` through the existing opt-in seam

#### Scenario: Gate-enforced auto-claim blocks claim_run when gate is blocked

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** auto-claim and gate enforcement are enabled
- **AND** the explicit auto-claim enablement gate is blocked
- **THEN** SDK MUST NOT call `claim_run`
- **AND** SDK MUST return fail-closed worker ownership evidence
- **AND** the evidence MUST include the nested enablement gate status and blocked reason

#### Scenario: Gate-enforced auto-claim blocks non-allowlisted entrypoint

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** auto-claim and gate enforcement are enabled
- **AND** the requested recovery entrypoint is not allowlisted by the enablement gate
- **THEN** SDK MUST NOT call `claim_run`
- **AND** the fail-closed evidence MUST identify `entrypoint_not_allowlisted`

#### Scenario: Gate-enforced auto-claim allows claim_run when gate is ready

- **WHEN** SDK recovery runs without descriptor ownership evidence
- **AND** auto-claim and gate enforcement are enabled
- **AND** the explicit auto-claim enablement gate is ready
- **THEN** SDK MAY call `claim_run`
- **AND** it MUST still record compact ownership evidence only

### Requirement: Runtime worker ownership contract MUST include production gate evidence

The runtime worker ownership contract MUST expose production gate evidence alongside adapter kind, durable status, enforcement mode, operations, fail-closed reasons, and operational readiness.

#### Scenario: Contract exposes blocked production gate

- **WHEN** the default runtime worker ownership contract is inspected
- **THEN** it includes `production_gate`
- **AND** the gate reports whether production default ownership is enabled
- **AND** missing production readiness sections are machine-readable

### Requirement: Production gate MUST fail closed for default recovery ownership

The runtime MUST NOT infer default recovery ownership authorization from durable adapter presence alone.

#### Scenario: Durable adapter exists but gate is blocked

- **WHEN** the worker ownership adapter is durable
- **AND** production gate evidence is blocked
- **THEN** SDK recovery ownership remains descriptor-evidence driven
- **AND** recovery entry auto-claim remains explicitly configured rather than default-enabled

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes vendor lock semantics evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `vendor_lock_semantics` section evidence MUST include vendor lock status, current posture, SQL-row-lease posture, missing lock semantics sections, production lock allowment, lock adapter, lock scope, fencing guarantee, failover semantics, TTL/renewal semantics, and stale owner cleanup evidence
- **AND** SQL row lease/fencing MUST NOT be treated as vendor lock semantics

#### Scenario: Production gate remains blocked when vendor lock semantics are absent

- **WHEN** the worker ownership adapter is durable SQL but no vendor-specific lock semantics are present
- **THEN** the worker ownership production gate remains blocked
- **AND** `vendor_lock_semantics` remains listed in `missing_sections`

#### Scenario: Production gate exposes renewal supervisor evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `heartbeat_renewal_supervisor` section evidence MUST include renewal supervisor status, missing sections, default enabled flag, explicit renew-once support, owner identity requirement, TTL/interval policy readiness, and lease-loss fail-closed evidence
- **AND** the evidence MUST NOT imply a background renewal supervisor has started

### Requirement: Runtime worker ownership MUST expose an opt-in renewal supervisor seam

The runtime MUST provide a renewal supervisor seam that can renew worker ownership leases only when explicitly invoked and MUST NOT start background work by default.

#### Scenario: Explicit renewal refreshes a valid lease

- **GIVEN** a worker owns a valid lease
- **WHEN** the renewal supervisor is explicitly asked to renew once with matching run id, worker id, lease id, and fencing token
- **THEN** it MUST call the ownership store heartbeat path
- **AND** it MUST return compact renewal evidence with `renewal_status = renewed`
- **AND** it MUST NOT start a thread, timer, worker, or loop

#### Scenario: Explicit renewal fails closed on stale evidence

- **GIVEN** a worker lease exists
- **WHEN** the renewal supervisor is asked to renew once with stale fencing, mismatched identity, expired ownership, or no store
- **THEN** it MUST return compact blocked evidence
- **AND** it MUST include the ownership failure reason when available
- **AND** it MUST NOT authorize recovery execution

#### Scenario: Controlled lifecycle is inactive by default

- **WHEN** a renewal supervisor is constructed
- **THEN** `status()` MUST report `controlled_lifecycle_supported = true`
- **AND** it MUST report `starts_by_default = false`
- **AND** no thread, timer, worker, or renewal loop MUST start automatically

#### Scenario: Explicit lifecycle start renews through one-shot primitive

- **GIVEN** a worker owns a valid lease
- **WHEN** `start(...)` is called with matching run id, worker id, lease id, and fencing token
- **THEN** the supervisor MUST first renew through the same `renew_once(...)` path
- **AND** `status()` MUST expose active lifecycle evidence and `last_renewal_status = "renewed"`
- **AND** the lifecycle MUST remain opt-in and non-authorizing for production recovery

#### Scenario: Explicit stop ends controlled lifecycle

- **GIVEN** a renewal supervisor has been explicitly started
- **WHEN** `stop()` is called
- **THEN** `status()` MUST report inactive
- **AND** the supervisor MUST NOT continue renewal loop work

#### Scenario: Controlled lifecycle fails closed on ownership loss

- **WHEN** lifecycle start or renewal encounters stale fencing, expired ownership, mismatched identity, or no store
- **THEN** the supervisor MUST enter an inactive or blocked state
- **AND** it MUST preserve compact blocked renewal evidence
- **AND** it MUST NOT grant default production recovery authorization

#### Scenario: Production gate exposes rollout readiness evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `rollout_checklist` section evidence MUST include rollout status, missing rollout sections, production rollout confirmation, strict-mode rollout, fallback policy, migration, stale fencing, and rollback plan evidence
- **AND** the evidence MUST NOT imply production ownership has been enabled

#### Scenario: Production gate exposes rollout operationalization evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `rollout_checklist` section evidence MUST include rollout operationalization status, rollout mode, missing rollout artifacts, rollback plan status, fallback policy status, renewal lifecycle verification status, and auto-claim decision status
- **AND** the evidence MUST NOT imply production rollout has been confirmed
- **AND** it MUST NOT enable production default worker ownership

### Requirement: Runtime MUST expose worker ownership rollout confirmation decision evidence

The worker ownership runtime contract MUST expose a machine-readable production rollout confirmation decision record without executing rollout or enabling production ownership by default.

#### Scenario: Rollout confirmation decision defaults to blocked

- **WHEN** the rollout confirmation decision contract is built without approval evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST report `production_rollout_confirmed = false`
- **AND** it MUST identify missing decision sections
- **AND** it MUST NOT enable production worker ownership

#### Scenario: Rollout operationalization embeds confirmation decision

- **WHEN** the rollout operationalization contract is built
- **THEN** it MUST expose the confirmation decision contract
- **AND** it MUST expose the decision status, decision id, approver, target store mode, and missing decision sections
- **AND** it MUST remain blocked when the decision record is blocked

#### Scenario: Ready decision remains only a rollout artifact

- **WHEN** all rollout confirmation decision inputs are ready
- **THEN** the decision contract MAY report `overall_status = ready`
- **AND** it MAY report `production_rollout_confirmed = true`
- **AND** it MUST NOT by itself enable production default worker ownership

#### Scenario: Production gate exposes auto-claim policy evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `recovery_entry_auto_claim_policy` section evidence MUST include policy status, missing policy sections, default enabled flag, descriptor-evidence fallback, gate readiness requirement, entrypoint allowlist, and audit requirement evidence
- **AND** the evidence MUST NOT imply recovery entry auto-claim has run or is enabled by default

### Requirement: Runtime MUST expose recovery auto-claim entrypoint allowlist evidence

The worker ownership runtime contract MUST expose a read-only allowlist contract for recovery-entry auto-claim entrypoints without enabling auto-claim by default.

#### Scenario: Auto-claim allowlist defaults to named entrypoints

- **WHEN** the worker ownership auto-claim entrypoint allowlist contract is built with defaults
- **THEN** it MUST report `overall_status = "ready"`
- **AND** it MUST include `submit_approval.approved` in `allowed_entrypoints`
- **AND** it MUST include `resume_run.continue_loop` in `allowed_entrypoints`
- **AND** it MUST report `default_auto_claim_enabled = false`
- **AND** it MUST report `requires_production_gate_ready = true`

#### Scenario: Auto-claim policy embeds allowlist evidence without enabling auto-claim

- **WHEN** the worker ownership auto-claim policy contract is built
- **THEN** it MUST include the nested entrypoint allowlist contract in `policy.entrypoint_allowlist`
- **AND** it MUST set `policy.entrypoint_allowlist_ready = true` when the nested allowlist is ready
- **AND** it MUST keep `auto_claim_enabled_by_default = false` unless the full policy is ready and explicitly enabled
- **AND** it MUST NOT call `claim_run`

### Requirement: Runtime MUST expose explicit auto-claim enablement gate evidence

The worker ownership runtime contract MUST expose a read-only explicit enablement gate for recovery-entry auto-claim and MUST keep auto-claim disabled unless the gate is ready.

#### Scenario: Explicit auto-claim enablement gate defaults to blocked

- **WHEN** the explicit auto-claim enablement gate contract is built with defaults
- **THEN** it MUST report `overall_status = "blocked"`
- **AND** it MUST report `will_auto_claim = false`
- **AND** it MUST include `explicit_runtime_configuration` in `missing_sections`
- **AND** it MUST include `production_gate_ready` in `missing_sections`
- **AND** it MUST NOT call `claim_run`

#### Scenario: Non-allowlisted entrypoint fails closed

- **WHEN** an explicit auto-claim enablement gate is built for an entrypoint outside the allowlist
- **THEN** it MUST report `overall_status = "blocked"`
- **AND** it MUST report `blocked_reason = "entrypoint_not_allowlisted"`
- **AND** it MUST report `will_auto_claim = false`

#### Scenario: Ready prerequisites allow explicit auto-claim decision

- **WHEN** explicit configuration, production gate readiness, durable ownership, idempotency evidence, audit evidence, lease validation, rollout decision, and allowlisted entrypoint evidence are all present
- **THEN** the gate MAY report `overall_status = "ready"`
- **AND** it MAY report `will_auto_claim = true`
- **AND** it still MUST NOT call `claim_run`

#### Scenario: Production gate exposes ownership audit evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `ownership_audit_evidence` section evidence MUST include audit evidence status, missing audit sections, compact ownership evidence, operation history readiness, recovery operation link readiness, timeline writer readiness, idempotent dedupe readiness, and authorization-source posture
- **AND** the evidence MUST NOT imply audit evidence authorizes ownership or recovery execution

#### Scenario: Production gate exposes default enablement strategy evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `fail_closed_default_decision` section evidence MUST include enablement strategy status, blocking sections, explicit enablement requirement, requested default enablement flag, production default allowment, all-required-sections readiness, fail-closed posture, and SQL-row-lease-not-default-authority evidence
- **AND** the evidence MUST NOT imply worker ownership has become default production execution authority

#### Scenario: Production gate remains blocked when audit evidence is not ready

- **WHEN** ownership audit evidence is compact but operation history, recovery operation link, timeline writer, or idempotent dedupe evidence is missing
- **THEN** the worker ownership production gate remains blocked
- **AND** `ownership_audit_evidence` remains listed in `missing_sections`

#### Scenario: Production gate is consumed by durable recovery

- **WHEN** durable recovery production gating consumes `worker_ownership.production_gate`
- **THEN** the ownership gate MUST remain descriptive evidence only
- **AND** SQL row lease/fencing MUST NOT be treated as production recovery authorization
- **AND** production ownership enforcement MUST remain disabled unless the ownership gate is ready and explicitly enabled

### Requirement: Runtime worker ownership MUST expose vendor lock target decision evidence

The runtime worker ownership contract MUST expose a read-only vendor lock target decision before vendor-specific distributed lock semantics can be treated as production-ready.

#### Scenario: Default target decision is blocked

- **WHEN** the runtime worker ownership contract is inspected without a vendor lock target decision
- **THEN** `worker_ownership.vendor_lock_semantics.policy.target_decision.overall_status` MUST be `blocked`
- **AND** `target_backend`, `lock_adapter_kind`, `lock_scope`, `fencing_strategy`, `ttl_renewal_strategy`, `failover_strategy`, and `stale_owner_cleanup_strategy` gaps MUST be machine-readable
- **AND** `sql_row_lease_is_vendor_lock` MUST be false
- **AND** `production_lock_allowed` MUST be false

#### Scenario: Target decision is embedded in vendor lock semantics

- **WHEN** `worker_ownership.vendor_lock_semantics` is inspected
- **THEN** its policy MUST include `target_decision`
- **AND** a blocked target decision MUST keep vendor lock semantics blocked

#### Scenario: Target decision remains non-executable

- **WHEN** a target backend, adapter kind, scope, fencing strategy, TTL/renewal strategy, failover strategy, stale owner cleanup strategy, and production allowment are recorded
- **THEN** the target decision MAY report `overall_status = ready`
- **AND** it MUST NOT create or start a vendor lock adapter
- **AND** it MUST NOT treat SQL row lease/fencing as vendor-specific distributed lock semantics

### Requirement: Runtime worker ownership MUST expose vendor lock adapter seam evidence

The runtime worker ownership contract MUST expose a side-effect-free vendor lock adapter seam contract before vendor-specific lock semantics can be considered production-ready.

#### Scenario: Vendor lock adapter seam defaults to blocked

- **WHEN** the vendor lock adapter seam contract is built without adapter metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing sections for adapter kind, target backend, lock scope, fencing strategy, TTL/renewal strategy, failover strategy, stale owner cleanup, acquire support, renew support, release support, probe support, and production allowment
- **AND** it MUST report SQL row lease/fencing as non-vendor-lock authority

#### Scenario: Vendor lock semantics embeds adapter seam

- **WHEN** `worker_ownership.vendor_lock_semantics` is inspected
- **THEN** its policy MUST include `adapter_contract`
- **AND** a blocked adapter contract MUST keep vendor lock semantics blocked
- **AND** the runtime MUST NOT acquire, renew, release, or probe a vendor lock as a side effect

#### Scenario: Ready adapter seam remains descriptive

- **WHEN** a vendor lock adapter seam includes adapter kind, target backend, scope, fencing, TTL/renewal, failover, stale cleanup, acquire/renew/release/probe support, and production allowment
- **THEN** the adapter seam MAY report `overall_status = ready`
- **AND** it MUST still not enable production default worker ownership by itself

### Requirement: Runtime worker ownership MUST expose PostgreSQL vendor lock probe evidence

The runtime worker ownership contract MUST expose a side-effect-free PostgreSQL advisory lock probe contract before a PostgreSQL vendor lock adapter can be considered production-ready.

#### Scenario: PostgreSQL probe defaults to blocked

- **WHEN** the PostgreSQL advisory lock probe contract is built without backend metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing sections for advisory lock family, lock key derivation, lock scope, fencing token binding, TTL/renewal strategy, failover behavior, stale owner cleanup, and probe safety
- **AND** it MUST report `executes_probe = false`
- **AND** it MUST report SQL row lease/fencing as non-vendor-lock authority

#### Scenario: Vendor lock adapter embeds PostgreSQL probe evidence

- **WHEN** `worker_ownership.vendor_lock_semantics.policy.adapter_contract` is inspected for a PostgreSQL adapter
- **THEN** it MUST include `backend_probe`
- **AND** a blocked PostgreSQL probe MUST keep the adapter contract blocked
- **AND** the runtime MUST NOT connect to PostgreSQL or execute advisory lock SQL as a side effect

#### Scenario: Ready PostgreSQL probe remains descriptive

- **WHEN** PostgreSQL advisory lock family, key derivation, scope, fencing binding, TTL/renewal, failover, stale cleanup, and probe safety evidence are complete
- **THEN** the probe MAY report `overall_status = ready`
- **AND** it MUST still not enable production default worker ownership by itself

### Requirement: Runtime worker ownership MUST expose a PostgreSQL advisory lock execution seam

The runtime worker ownership contract MUST expose an opt-in PostgreSQL advisory lock execution seam for vendor lock hardening. The seam MUST remain inactive unless a caller explicitly injects an executor boundary.

#### Scenario: Execution seam defaults to blocked without executor

- **WHEN** a PostgreSQL advisory lock execution seam is constructed without an executor
- **THEN** its contract MUST report `executor_bound = false`
- **AND** one-shot operations MUST return blocked evidence
- **AND** no database connection or advisory lock SQL MUST be executed
- **AND** production worker ownership MUST NOT be enabled

#### Scenario: Explicit executor can probe and acquire once

- **WHEN** a caller injects an executor and invokes the PostgreSQL advisory lock execution seam explicitly
- **THEN** the seam MAY build probe and acquire operation envelopes
- **AND** the envelopes MUST include operation kind, lock key, run identity when applicable, worker identity, and fencing token evidence
- **AND** executor denial MUST return blocked evidence rather than production authorization

#### Scenario: Execution seam requires owner identity and fencing

- **WHEN** acquire, renew, or release is requested without run id, worker id, or fencing token evidence
- **THEN** the seam MUST fail closed before invoking the executor
- **AND** the blocked reason MUST be machine-readable
- **AND** recovery entry auto-claim MUST NOT run as a side effect

#### Scenario: PostgreSQL probe embeds execution seam evidence

- **WHEN** PostgreSQL vendor lock probe evidence is inspected
- **THEN** it MUST include nested execution seam evidence
- **AND** missing executor evidence MUST keep the execution seam blocked
- **AND** ready probe metadata alone MUST NOT imply advisory lock execution or production ownership enablement

### Requirement: Runtime worker ownership MUST expose production default enablement input source evidence

The worker ownership runtime contract MUST expose a read-only input source contract for production default ownership enablement requests.

#### Scenario: Enablement input source defaults to blocked

- **WHEN** the production default enablement input source contract is built without source metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source, request, approval, target store mode, rollout artifact, vendor lock decision, renewal lifecycle, auto-claim decision, audit, rollback, and fallback evidence
- **AND** it MUST NOT enable production default worker ownership

#### Scenario: Enablement strategy embeds input source evidence

- **WHEN** the production enablement strategy is built
- **THEN** it MUST include the nested input source contract
- **AND** blocked input source evidence MUST keep production default allowment false even when an explicit enablement boolean is requested

#### Scenario: Complete input source remains descriptive

- **WHEN** a production default enablement input source includes a valid source kind, request id, requester, approval time, strict SQL target mode, rollout artifact, vendor lock decision, renewal lifecycle reference, auto-claim decision, audit evidence, rollback plan, and fallback policy
- **THEN** the input source MAY report `overall_status = ready`
- **AND** it MUST remain descriptive evidence until all production gate sections are ready and explicit default enablement is requested

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
### Requirement: Runtime worker ownership MUST expose PostgreSQL rollout artifact consumer evidence

The worker ownership runtime contract MUST provide a read-only consumer for PostgreSQL advisory lock rollout artifact or runtime config evidence.

#### Scenario: Consumer defaults to blocked and non-executing

- **WHEN** the PostgreSQL rollout artifact consumer is built without an artifact/config payload
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source kind, artifact id, approval, target mode, target backend, adapter, rollout artifact, vendor lock decision, renewal lifecycle, auto-claim, audit, rollback, fallback, and PostgreSQL execution seam evidence
- **AND** it MUST report `will_enable_production_default = false`
- **AND** it MUST report `executes_advisory_lock = false`

#### Scenario: Complete artifact produces enablement input source evidence

- **WHEN** the consumer receives a complete rollout artifact for `strict_sql` + `postgres` + `postgres_advisory_lock` and a ready PostgreSQL execution seam contract
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include a nested `enablement_input_source` contract with `overall_status = ready`
- **AND** it MUST NOT execute PostgreSQL advisory lock SQL
- **AND** it MUST NOT enable production default worker ownership

#### Scenario: Blocked execution seam keeps consumer blocked

- **WHEN** the rollout artifact is complete but PostgreSQL execution seam evidence is blocked
- **THEN** the consumer MUST report `overall_status = blocked`
- **AND** it MUST include `postgres_execution_seam` in `missing_sections`
- **AND** the nested enablement input source MUST NOT be treated as default production authorization

### Requirement: Runtime worker ownership MUST expose PostgreSQL target artifact binding evidence

The worker ownership runtime contract MUST provide a read-only binding that maps PostgreSQL rollout artifact/config evidence to vendor lock target decision evidence.

#### Scenario: Target artifact binding defaults to blocked

- **WHEN** the PostgreSQL target artifact binding is built without artifact/config evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source, artifact, approval, backend, adapter, target decision, rollout consumer, and source reference sections
- **AND** it MUST report `will_enable_production_lock = false`
- **AND** it MUST report `executes_advisory_lock = false`

#### Scenario: Complete artifact produces nested target decision evidence

- **WHEN** the binding receives a complete PostgreSQL rollout artifact and ready rollout consumer evidence
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include nested ready `target_decision_input`
- **AND** it MUST include nested ready `target_decision`
- **AND** it MUST still report `will_enable_production_lock = false`
- **AND** it MUST still report `executes_advisory_lock = false`

#### Scenario: SQL row lease is never promoted by binding

- **WHEN** strict SQL row lease/fencing is present
- **THEN** the binding MUST report `sql_row_lease_is_vendor_lock = false`
- **AND** it MUST NOT use SQL row lease/fencing as PostgreSQL advisory lock authority

### Requirement: Runtime worker ownership MUST expose PostgreSQL vendor lock semantics binding evidence

The worker ownership runtime contract MUST provide a read-only binding that maps PostgreSQL target artifact binding evidence into a vendor lock semantics candidate.

#### Scenario: Semantics binding defaults to blocked

- **WHEN** the PostgreSQL vendor lock semantics binding is built without target artifact binding and execution seam evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing target binding, execution seam, probe, adapter, and semantics sections
- **AND** it MUST report `will_enable_production_lock = false`
- **AND** it MUST report `will_update_production_gate = false`
- **AND** it MUST report `executes_advisory_lock = false`

#### Scenario: Complete target binding produces semantics candidate

- **WHEN** the binding receives ready PostgreSQL target artifact binding evidence and ready opt-in execution seam evidence
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include ready nested PostgreSQL probe evidence
- **AND** it MUST include ready nested vendor lock adapter evidence
- **AND** it MUST include ready nested vendor lock semantics candidate evidence
- **AND** it MUST still report `will_enable_production_lock = false`
- **AND** it MUST still report `will_update_production_gate = false`
- **AND** it MUST still report `executes_advisory_lock = false`

#### Scenario: SQL row lease is not promoted by semantics binding

- **WHEN** strict SQL row lease/fencing exists
- **THEN** the binding MUST report `sql_row_lease_is_vendor_lock = false`
- **AND** it MUST NOT treat SQL row lease/fencing as PostgreSQL advisory lock authority

### Requirement: Runtime worker ownership MUST expose PostgreSQL production gate wiring decision evidence

The worker ownership runtime contract MUST provide a read-only decision that records whether a PostgreSQL vendor lock semantics candidate is explicitly approved as future production gate input.

#### Scenario: Wiring decision defaults to blocked

- **WHEN** the wiring decision is built without semantics candidate evidence or approval metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing semantics binding, decision, approval, rollout, rollback, and fallback sections
- **AND** it MUST report `wiring_allowed = false`
- **AND** it MUST report `will_update_production_gate = false`
- **AND** it MUST report `will_enable_production_lock = false`

#### Scenario: Complete decision allows future wiring without side effects

- **WHEN** the wiring decision receives ready PostgreSQL semantics binding evidence and explicit approval metadata
- **THEN** it MAY report `overall_status = ready`
- **AND** it MAY report `wiring_allowed = true`
- **AND** it MUST still report `will_update_production_gate = false`
- **AND** it MUST still report `will_enable_production_lock = false`
- **AND** it MUST still report `executes_advisory_lock = false`

#### Scenario: SQL row lease is not promoted by wiring decision

- **WHEN** strict SQL row lease/fencing exists
- **THEN** the wiring decision MUST report `sql_row_lease_is_vendor_lock = false`
- **AND** it MUST NOT treat SQL row lease/fencing as production vendor lock authority

### Requirement: Runtime worker ownership MUST expose production gate composition dry-run evidence

The worker ownership runtime contract MUST provide a side-effect-free production gate composition dry-run that combines required production readiness evidence without enabling production defaults.

#### Scenario: Composition dry-run defaults to blocked

- **WHEN** the dry-run is built without complete production readiness evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing vendor lock wiring, renewal supervisor, rollout confirmation, auto-claim enablement, ownership audit, and production default enablement input sections
- **AND** it MUST report `production_default_would_be_allowed = false`
- **AND** it MUST report `will_enable_production_default = false`
- **AND** it MUST report `executes_lock = false`
- **AND** it MUST report `starts_background_worker = false`
- **AND** it MUST report `runs_recovery_auto_claim = false`

#### Scenario: Complete evidence can dry-run as ready

- **WHEN** vendor lock wiring, renewal lifecycle, rollout confirmation, auto-claim enablement, ownership audit, and production default enablement input evidence are all ready
- **THEN** the dry-run MAY report `overall_status = ready`
- **AND** it MAY report `all_required_sections_ready = true`
- **AND** it MAY report `production_default_would_be_allowed = true`
- **AND** it MUST still report `will_enable_production_default = false`
- **AND** it MUST still report `executes_lock = false`
- **AND** it MUST still report `starts_background_worker = false`
- **AND** it MUST still report `runs_recovery_auto_claim = false`

#### Scenario: Dry-run does not bypass production recovery gate

- **WHEN** the dry-run evidence is ready
- **THEN** durable recovery production gate MUST remain blocked unless the real worker ownership production gate and durable rollout enablement are explicitly ready
- **AND** the dry-run MUST NOT become an authorization source by itself

### Requirement: Runtime worker ownership MUST expose production enablement runtime config consumer evidence

The worker ownership runtime contract MUST provide a side-effect-free consumer that normalizes caller-owned production enablement runtime config into production default enablement input source evidence and production gate composition dry-run evidence.

#### Scenario: Runtime config consumer defaults to blocked

- **WHEN** the production enablement runtime config consumer is built without config metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source, config id, approval, target mode, target backend, lock adapter, rollout artifact, vendor lock decision, renewal lifecycle, auto-claim decision, audit evidence, rollback plan, fallback policy, enablement input source, and dry-run sections
- **AND** it MUST report `will_enable_production_default = false`
- **AND** it MUST report `executes_lock = false`
- **AND** it MUST report `starts_background_worker = false`
- **AND** it MUST report `runs_recovery_auto_claim = false`

#### Scenario: Complete runtime config produces ready nested evidence

- **WHEN** the consumer receives complete caller-owned config for `strict_sql` + `postgres` + `postgres_advisory_lock`
- **AND** ready production gate composition dry-run input contracts are supplied
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include a nested `enablement_input_source` with `overall_status = ready`
- **AND** it MUST include a nested `composition_dry_run` with `overall_status = ready`
- **AND** it MUST still report `will_enable_production_default = false`
- **AND** it MUST still report `executes_lock = false`
- **AND** it MUST still report `starts_background_worker = false`
- **AND** it MUST still report `runs_recovery_auto_claim = false`

#### Scenario: Runtime config consumer is not authorization

- **WHEN** runtime config consumer evidence is ready
- **THEN** durable recovery production gate MUST remain blocked unless the real worker ownership production gate and durable rollout enablement are explicitly ready
- **AND** the consumer MUST NOT mutate production gate state or enable default worker ownership by itself

### Requirement: Runtime factory MUST bind production enablement config consumer input

The embedded runtime factory MUST accept caller-owned worker ownership production enablement config metadata as an explicit contract assembly input and MUST expose the resulting runtime config consumer evidence through `worker_ownership.production_enablement_runtime_config_consumer`.

#### Scenario: Default factory binding remains blocked

- **WHEN** the default embedded runtime factory is built without worker ownership production enablement config
- **THEN** `worker_ownership.production_enablement_runtime_config_consumer.overall_status` MUST be `blocked`
- **AND** it MUST report `will_enable_production_default = false`
- **AND** it MUST report `executes_lock = false`
- **AND** it MUST report `starts_background_worker = false`
- **AND** it MUST report `runs_recovery_auto_claim = false`

#### Scenario: Complete factory config produces descriptive ready evidence

- **WHEN** the embedded runtime factory receives complete caller-owned config for `strict_sql` + `postgres` + `postgres_advisory_lock`
- **AND** the required dry-run input contracts are ready
- **THEN** `worker_ownership.production_enablement_runtime_config_consumer.overall_status` MAY be `ready`
- **AND** nested enablement input source evidence MUST be `ready`
- **AND** nested composition dry-run evidence MUST be `ready`
- **AND** the contract MUST still report `will_enable_production_default = false`
- **AND** the contract MUST still report `executes_lock = false`
- **AND** the contract MUST still report `starts_background_worker = false`
- **AND** the contract MUST still report `runs_recovery_auto_claim = false`

### Requirement: Runtime Surface MUST pass only local materialized config to the factory

Runtime Surface MUST bind worker ownership production enablement config to the embedded runtime factory only from already materialized effective config metadata. The binding MUST NOT read files, remote config, secret stores, or execute lock operations.

#### Scenario: Runtime profile reflects configured local evidence

- **WHEN** Runtime Surface effective config contains a local `worker_ownership_production_enablement_config` object
- **THEN** Runtime Profile MUST expose factory-built consumer evidence derived from that object
- **AND** Runtime Surface MUST NOT read external config sources as part of contract assembly
- **AND** Runtime Surface MUST NOT enable production worker ownership by side effect
