# durable-recovery-loader Specification

## Purpose

Define the durable recovery loader that reconstructs recovery candidates from persisted workspace state without treating in-process state as durable storage.

## Requirements

### Requirement: Loader MUST reconstruct recovery candidates from durable workspace state

The loader MUST read persisted run state, events, approval state, continuation descriptors, and recovery operation history from a durable workspace backend.

#### Scenario: Durable state is complete

- **WHEN** persisted state contains a valid checkpoint, resume cursor, and resolvable continuation binding
- **THEN** the loader produces a registry-backed recovery candidate
- **AND** it exposes descriptor lifecycle evidence
- **AND** it does not execute recovery by itself

#### Scenario: Durable state is incomplete

- **WHEN** persisted state is missing, stale, unsafe, or lacks a resolvable registry binding
- **THEN** the loader fails closed
- **AND** it returns a machine-readable recovery reason
- **AND** it exposes descriptor lifecycle evidence when descriptors are present

### Requirement: Loader MUST NOT deserialize executable callables

The loader MUST only reattach executable continuations through registered binding identities.

#### Scenario: Descriptor contains raw callable-like payload

- **WHEN** persisted descriptor contains executable payload data instead of binding identity
- **THEN** the loader rejects the descriptor
- **AND** recovery remains blocked

### Requirement: Runtime quality gates MUST cover durable loader evidence

The runtime contract smoke and quality gate summary MUST expose durable recovery loader evidence.

#### Scenario: Smoke proves ready and fail-closed paths

- **WHEN** runtime contract smoke runs
- **THEN** it MUST include a `durable_recovery_loader` check
- **AND** the check MUST cover a ready registry-backed candidate, a missing run snapshot, unresolved binding, stale approval state, and unsafe descriptor rejection
- **AND** the check MUST expose descriptor lifecycle states for quality gate consumption

### Requirement: Durable loader MUST expose production recovery gate boundary

The durable recovery loader contract MUST identify that candidate loading is not recovery execution and remains gated by the production recovery gate.

#### Scenario: Loader is ready but production gate is blocked

- **WHEN** the loader produces a ready registry-backed candidate
- **AND** production recovery gate is blocked
- **THEN** the loader result remains non-executing evidence
- **AND** default cross-process recovery execution remains disabled

### Requirement: Loader handoff MUST be explicit

The runtime MUST require explicit handoff policy before a loaded candidate can be executed as production cross-process recovery.

#### Scenario: Handoff policy is missing

- **WHEN** a recovery candidate is loaded
- **AND** loader execution handoff policy is missing
- **THEN** DurableRecoveryLoader MUST NOT execute the candidate
- **AND** the production gate includes `loader_execution_handoff_policy` in missing sections

#### Scenario: Handoff policy is present but executor is missing

- **WHEN** a recovery candidate is loaded
- **AND** loader execution handoff policy is available
- **AND** no recovery executor binding exists
- **THEN** DurableRecoveryLoader MUST NOT execute the candidate
- **AND** the candidate includes handoff policy evidence with `will_execute = false`
