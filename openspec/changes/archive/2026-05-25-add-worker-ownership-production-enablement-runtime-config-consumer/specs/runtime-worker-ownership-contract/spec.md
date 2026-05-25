## ADDED Requirements

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
