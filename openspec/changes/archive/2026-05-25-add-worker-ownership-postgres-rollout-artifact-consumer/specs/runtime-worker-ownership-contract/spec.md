## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose PostgreSQL rollout artifact consumer evidence

The worker ownership runtime contract MUST provide a read-only consumer for PostgreSQL advisory lock rollout artifact or runtime config evidence.

#### Scenario: Consumer defaults to blocked and non-executing

- **WHEN** the PostgreSQL rollout artifact consumer is built without an artifact/config payload
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source kind, artifact id, approval, target mode, target backend, adapter, rollout artifact, vendor lock decision, renewal lifecycle, auto-claim, audit, rollback, fallback, and PostgreSQL execution seam evidence
- **AND** it MUST report `will_enable_production_default = false`
- **AND** it MUST report `executes_advisory_lock = false`

#### Scenario: Complete artifact produces enablement input source evidence

- **WHEN** the consumer receives a complete rollout artifact for `strict_sql` + `postgres` + `postgres_advisory_lock` and a ready PostgreSQL execution seam contract
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include a nested `enablement_input_source` contract with `overall_status = ready`
- **AND** it MUST NOT execute PostgreSQL advisory lock SQL
- **AND** it MUST NOT enable production default worker ownership

#### Scenario: Blocked execution seam keeps consumer blocked

- **WHEN** the rollout artifact is complete but PostgreSQL execution seam evidence is blocked
- **THEN** the consumer MUST report `overall_status = blocked`
- **AND** it MUST include `postgres_execution_seam` in `missing_sections`
- **AND** the nested enablement input source MUST NOT be treated as default production authorization
