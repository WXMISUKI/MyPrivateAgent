## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose production gate composition dry-run evidence

The worker ownership runtime contract MUST provide a side-effect-free production gate composition dry-run that combines required production readiness evidence without enabling production defaults.

#### Scenario: Composition dry-run defaults to blocked

- **WHEN** the dry-run is built without complete production readiness evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing vendor lock wiring, renewal supervisor, rollout confirmation, auto-claim enablement, ownership audit, and production default enablement input sections
- **AND** it MUST report `production_default_would_be_allowed = false`
- **AND** it MUST report `will_enable_production_default = false`
- **AND** it MUST report `executes_lock = false`
- **AND** it MUST report `starts_background_worker = false`
- **AND** it MUST report `runs_recovery_auto_claim = false`

#### Scenario: Complete evidence can dry-run as ready

- **WHEN** vendor lock wiring, renewal lifecycle, rollout confirmation, auto-claim enablement, ownership audit, and production default enablement input evidence are all ready
- **THEN** the dry-run MAY report `overall_status = ready`
- **AND** it MAY report `all_required_sections_ready = true`
- **AND** it MAY report `production_default_would_be_allowed = true`
- **AND** it MUST still report `will_enable_production_default = false`
- **AND** it MUST still report `executes_lock = false`
- **AND** it MUST still report `starts_background_worker = false`
- **AND** it MUST still report `runs_recovery_auto_claim = false`

#### Scenario: Dry-run does not bypass production recovery gate

- **WHEN** the dry-run evidence is ready
- **THEN** durable recovery production gate MUST remain blocked unless the real worker ownership production gate and durable rollout enablement are explicitly ready
- **AND** the dry-run MUST NOT become an authorization source by itself
