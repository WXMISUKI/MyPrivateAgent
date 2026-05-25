# durable-recovery-loader Specification

## Purpose

Define the durable recovery loader that reconstructs recovery candidates from persisted workspace state without treating in-process state as durable storage.

## ADDED Requirements

### Requirement: Loader MUST reconstruct recovery candidates from durable workspace state

The loader MUST read persisted run state, events, approval state, continuation descriptors, and recovery operation history from a durable workspace backend.

#### Scenario: Durable state is complete

- **WHEN** persisted state contains a valid checkpoint, resume cursor, and resolvable continuation binding
- **THEN** the loader produces a registry-backed recovery candidate
- **AND** it does not execute recovery by itself

#### Scenario: Durable state is incomplete

- **WHEN** persisted state is missing, stale, unsafe, or lacks a resolvable registry binding
- **THEN** the loader fails closed
- **AND** it returns a machine-readable recovery reason

### Requirement: Loader MUST NOT deserialize executable callables

The loader MUST only reattach executable continuations through registered binding identities.

#### Scenario: Descriptor contains raw callable-like payload

- **WHEN** persisted descriptor contains executable payload data instead of binding identity
- **THEN** the loader rejects the descriptor
- **AND** recovery remains blocked
