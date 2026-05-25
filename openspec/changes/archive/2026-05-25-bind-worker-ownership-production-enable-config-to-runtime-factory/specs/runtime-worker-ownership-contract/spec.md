## ADDED Requirements

### Requirement: Runtime factory MUST bind production enablement config consumer input

The embedded runtime factory MUST accept caller-owned worker ownership production enablement config metadata as an explicit contract assembly input and MUST expose the resulting runtime config consumer evidence through `worker_ownership.production_enablement_runtime_config_consumer`.

#### Scenario: Default factory binding remains blocked

- **WHEN** the default embedded runtime factory is built without worker ownership production enablement config
- **THEN** `worker_ownership.production_enablement_runtime_config_consumer.overall_status` MUST be `blocked`
- **AND** it MUST report missing config/input sections
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

#### Scenario: Runtime profile without config remains fail-closed

- **WHEN** Runtime Surface effective config omits worker ownership production enablement config
- **THEN** Runtime Profile MUST expose blocked runtime config consumer evidence
- **AND** production default ownership MUST remain disabled
