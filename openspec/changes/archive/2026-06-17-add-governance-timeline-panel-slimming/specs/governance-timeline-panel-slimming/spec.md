## ADDED Requirements

### Requirement: Governance Timeline panel styles MUST be extracted without behavior changes

The Governance Timeline panel slimming change MUST extract panel styles into a dedicated CSS file without changing runtime or governance semantics.

#### Scenario: Styles are extracted

- **WHEN** `GovernanceTimelinePanel.vue` is loaded
- **THEN** it imports the extracted `GovernanceTimelinePanel.css`
- **AND** existing selectors and visual behavior remain available
- **AND** no backend contract, runtime behavior, or governance payload shape changes
