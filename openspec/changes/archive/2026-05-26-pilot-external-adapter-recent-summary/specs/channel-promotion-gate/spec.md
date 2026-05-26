## ADDED Requirements

### Requirement: external_adapter Resume Decision MUST Target Recent Summary Only

The channel promotion gate MUST record that `external_adapter` implementation may resume only for the `recent_summary` layer until a separate decision promotes it further.

#### Scenario: Recent summary implementation is allowed

- **WHEN** `external_adapter_recent_summary` is implemented from Query Control trace evidence
- **THEN** the promotion gate MAY report `recent_summary_status = recorded`
- **AND** `external_adapter` MUST remain blocked for `query_detail`, `query_history`, and `query_workspace`

#### Scenario: Deeper layers remain blocked

- **WHEN** `external_adapter` recent summary evidence exists
- **THEN** the promotion gate MUST NOT treat it as a dedicated detail contract
- **AND** it MUST keep `ready_for_detail = false` until a separate detail readiness decision exists
