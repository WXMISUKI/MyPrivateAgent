# embedded-sdk-continuation-binding-catalog Specification

## Purpose
Define the Embedded SDK continuation binding catalog that identifies registry-backed continuation bindings without persisting executable callables.
## Requirements
### Requirement: Continuation Registry Must Expose A Stable Binding Catalog

`EmbeddedContinuationRegistry` implementations MUST be able to describe registered bindings through a stable catalog view.

#### Scenario: In-memory registry exposes binding metadata

- **GIVEN** an in-memory continuation registry contains registered bindings
- **WHEN** the registry catalog is requested
- **THEN** each binding entry MUST expose at least `binding_id`, `binding_kind`, and `handler_name`
- **AND** catalog output MUST NOT expose executable handler objects

### Requirement: Embedded SDK Must Expose Registry Catalog Through A Narrow Read Interface

The SDK MUST expose a read-only catalog interface for registered continuation bindings.

#### Scenario: Caller inspects registered continuation bindings

- **GIVEN** an SDK instance is constructed with a continuation registry
- **WHEN** the caller requests the continuation binding catalog
- **THEN** the SDK MUST return a machine-readable catalog
- **AND** the catalog MUST be safe to use for diagnostics and preflight checks
