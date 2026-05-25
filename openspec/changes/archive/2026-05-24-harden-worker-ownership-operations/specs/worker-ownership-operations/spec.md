# worker-ownership-operations Specification

## Purpose

Define production operational readiness for worker ownership beyond the existing lease/fencing seam.

## ADDED Requirements

### Requirement: Worker ownership MUST expose operational readiness

The runtime MUST expose whether worker ownership is ready for production operation, including adapter kind, durable status, renewal support, recovery-entry claim mode, and rollout checklist status.

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
