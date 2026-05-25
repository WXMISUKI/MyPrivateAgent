## ADDED Requirements

### Requirement: Continuation descriptor lifecycle MUST be machine-readable

The runtime MUST expose a compact lifecycle contract for persisted continuation descriptors before default production cross-process recovery can advance.

The contract MUST include:

- contract version
- allowed lifecycle states
- descriptor count
- observed states
- readiness flag
- unsafe descriptor keys
- fail-closed reason

#### Scenario: Descriptor is ready

- **WHEN** a persisted descriptor has binding identity
- **AND** all required bindings are resolved through the continuation registry
- **THEN** lifecycle evidence reports `ready`
- **AND** the loader may produce a non-executing recovery candidate

#### Scenario: Descriptor is bound but unresolved

- **WHEN** a persisted descriptor has binding identity
- **AND** one or more required bindings cannot be resolved
- **THEN** lifecycle evidence reports `bound`
- **AND** recovery remains blocked with `missing_registered_binding`

#### Scenario: Descriptor is unsafe

- **WHEN** a persisted descriptor contains callable-like payloads or runtime-only state
- **THEN** lifecycle evidence reports `unsafe`
- **AND** recovery remains blocked with `descriptor_corrupted`

#### Scenario: Descriptor is stale

- **WHEN** persisted approval or run state has already resolved the waiting point
- **THEN** lifecycle evidence reports `stale`
- **AND** recovery remains blocked with the corresponding stale state reason

### Requirement: Lifecycle governance MUST NOT execute recovery

Descriptor lifecycle governance MUST classify descriptors only. It MUST NOT execute recovery, deserialize callables, or authorize production default recovery by itself.

#### Scenario: Lifecycle is ready but handoff is missing

- **WHEN** lifecycle evidence reports ready
- **AND** loader execution handoff policy is missing
- **THEN** production recovery remains blocked
- **AND** DurableRecoveryLoader does not execute the candidate

### Requirement: Runtime quality gates MUST cover descriptor lifecycle evidence

Runtime contract smoke, Quality Gate summary, Runtime Contract Gate, and snapshot guard MUST expose descriptor lifecycle coverage.

#### Scenario: Smoke proves lifecycle states

- **WHEN** runtime contract smoke runs
- **THEN** it includes continuation descriptor lifecycle evidence
- **AND** the evidence covers ready, bound, stale, and unsafe states
