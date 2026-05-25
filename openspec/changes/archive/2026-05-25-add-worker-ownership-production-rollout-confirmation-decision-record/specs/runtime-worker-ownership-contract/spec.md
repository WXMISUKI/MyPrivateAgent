# runtime-worker-ownership-contract Delta

## ADDED Requirements

### Requirement: Runtime MUST expose worker ownership rollout confirmation decision evidence

The worker ownership runtime contract MUST expose a machine-readable production rollout confirmation decision record without executing rollout or enabling production ownership by default.

#### Scenario: Rollout confirmation decision defaults to blocked

- **WHEN** the rollout confirmation decision contract is built without approval evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST report `production_rollout_confirmed = false`
- **AND** it MUST identify missing decision sections
- **AND** it MUST NOT enable production worker ownership

#### Scenario: Rollout operationalization embeds confirmation decision

- **WHEN** the rollout operationalization contract is built
- **THEN** it MUST expose the confirmation decision contract
- **AND** it MUST expose the decision status, decision id, approver, target store mode, and missing decision sections
- **AND** it MUST remain blocked when the decision record is blocked

#### Scenario: Ready decision remains only a rollout artifact

- **WHEN** all rollout confirmation decision inputs are ready
- **THEN** the decision contract MAY report `overall_status = ready`
- **AND** it MAY report `production_rollout_confirmed = true`
- **AND** it MUST NOT by itself enable production default worker ownership
