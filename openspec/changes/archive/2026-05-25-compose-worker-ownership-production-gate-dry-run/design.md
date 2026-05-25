# Design

## Contract

Add `build_worker_ownership_production_gate_composition_dry_run_contract(...)`.

The builder consumes existing compact evidence:

- PostgreSQL production gate wiring decision.
- Renewal supervisor lifecycle/readiness.
- Rollout confirmation decision.
- Auto-claim enablement gate.
- Ownership audit evidence.
- Production default enablement input source.

It returns:

- `contract_version`
- `overall_status`
- `all_required_sections_ready`
- `production_default_would_be_allowed`
- `missing_sections`
- `blocking_reasons`
- `will_enable_production_default`
- `executes_lock`
- `starts_background_worker`
- `runs_recovery_auto_claim`
- nested compact statuses for each input
- `next_allowed_action`
- `non_goals`

## Readiness Rule

The dry-run MAY report `overall_status = ready` only when every required input is ready and explicit enablement input evidence is ready. Even in this ready state it MUST report:

- `will_enable_production_default = false`
- `executes_lock = false`
- `starts_background_worker = false`
- `runs_recovery_auto_claim = false`

The dry-run is evidence for a future explicit execution seam, not an execution seam itself.

## Default Behavior

Without injected evidence, the builder composes the existing default contracts. The default must remain blocked and machine-readable, with blocking sections including vendor lock wiring, renewal supervisor production readiness, rollout confirmation, auto-claim enablement, ownership audit, and production default enablement input.

## Quality Gates

Runtime smoke, Quality Gate, and Runtime Contract Gate should add coverage fields proving:

- default dry-run is blocked and non-executing;
- complete ready-evidence dry-run can become ready;
- ready dry-run still does not enable defaults or execute behavior;
- current production gate and durable recovery gate remain blocked by default.
