## Design

### Gate Evidence Linking

`EmbeddedRuntimeFactory.build_runtime_contract()` should build worker ownership operational readiness before the persistence interface. It should pass `worker_ownership_operational_readiness.production_gate` into `build_embedded_sdk_persistence_interface(...)`.

The persistence interface should pass that gate to `build_durable_workspace_production_recovery_gate_contract(...)`.

### Durable Recovery Gate Semantics

The durable recovery gate section named `worker_ownership_production_gate` should expose compact nested evidence:

- worker ownership gate contract version
- worker ownership gate status
- worker ownership production-default enabled flag
- worker ownership missing sections
- worker ownership next allowed action

This section is ready only when the nested ownership gate is `ready` and `production_default_enabled = true`. Current defaults must remain blocked.

### Quality Gate Semantics

Runtime smoke should assert that the durable recovery gate includes nested worker ownership evidence and that current defaults remain blocked because ownership and rollout are incomplete.

Quality Gate and Runtime Contract Gate should include the linked evidence in `embedded_sdk_persistence_coverage`, and old or malformed artifacts should fail closed.

### Non-Goals

- Do not implement or simulate a vendor lock adapter.
- Do not add a background lease renewal process.
- Do not enable recovery entry auto-claim by default.
- Do not start recovery execution from the durable loader.
