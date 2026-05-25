# worker-ownership-operations Specification

## Purpose

Define production operational readiness for worker ownership beyond the existing lease/fencing seam.

## Requirements

### Requirement: Worker ownership MUST expose operational readiness

The runtime MUST expose whether worker ownership is ready for production operation, including adapter kind, durable status, renewal support, recovery-entry claim mode, vendor lock posture, migration checklist, and rollout checklist status.

#### Scenario: Memory-only runtime

- **WHEN** the default memory-only ownership store is used
- **THEN** operational readiness is not production-ready
- **AND** the contract explains that lease evidence is local preview only

#### Scenario: Strict SQL runtime

- **WHEN** strict SQL ownership is configured and migrations are ready
- **THEN** operational readiness may report durable ownership capability
- **AND** it still distinguishes SQL row lease/fencing from vendor-specific distributed locks

### Requirement: Recovery entry claim MUST be explicit

Recovery entrypoints MUST only auto-claim ownership when explicit configuration enables the behavior.

#### Scenario: Auto-claim disabled

- **WHEN** a recovery entrypoint executes without auto-claim enabled
- **THEN** existing descriptor ownership evidence remains the enforcement source

#### Scenario: Auto-claim enabled

- **WHEN** a registry-backed recovery entrypoint executes with auto-claim enabled and an ownership store injected
- **THEN** the SDK MUST claim run ownership before executing the continuation
- **AND** the recovery operation MUST record compact worker ownership evidence

### Requirement: Runtime smoke MUST cover ownership operational readiness

The runtime contract smoke check MUST expose machine-readable ownership operational readiness evidence for default memory, strict SQL, and fallback store modes.

#### Scenario: Smoke validates production readiness boundaries

- **WHEN** `runtime_contract_smoke.py` emits the `worker_ownership_store_mode` check
- **THEN** it MUST show memory/fallback ownership as preview or degraded
- **AND** it MUST show strict SQL ownership as production-ready only with SQL row lease/fencing posture and migration readiness evidence

### Requirement: Worker ownership operations MUST expose a production gate

Operational readiness MUST include a production gate that distinguishes preview, durable SQL lease/fencing, and production-default ownership readiness.

#### Scenario: Memory or fallback posture

- **WHEN** worker ownership uses memory-only or fallback posture
- **THEN** the production gate reports `overall_status = blocked`
- **AND** production default ownership enforcement remains disabled

#### Scenario: Strict SQL posture without vendor lock

- **WHEN** strict SQL ownership is configured and migrations are ready
- **THEN** operational readiness may report durable row lease/fencing
- **AND** the production gate remains blocked unless vendor lock semantics, renewal supervision, rollout, auto-claim policy, and audit evidence are complete

### Requirement: Runtime smoke MUST cover production gate posture

The runtime contract smoke check MUST expose worker ownership production gate evidence.

#### Scenario: Smoke validates production gate blocked boundary

- **WHEN** `runtime_contract_smoke.py` emits the `worker_ownership_store_mode` check
- **THEN** it MUST include production gate contract version, status, missing sections, and default-enabled flag
- **AND** the check MUST prove production default ownership enforcement is disabled when the gate is blocked
