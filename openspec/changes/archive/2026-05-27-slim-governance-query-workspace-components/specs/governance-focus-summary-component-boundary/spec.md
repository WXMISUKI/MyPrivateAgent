## ADDED Requirements

### Requirement: Focus summary grid remains display-only
The governance timeline focus summary component SHALL render summary values from props and SHALL NOT own route state, backend loading, query selection state, or clipboard side effects.

#### Scenario: Parent owns orchestration
- **WHEN** the summary grid needs to clear a query, stage, dedupe key, framework adapter error type, or copy the active dedupe key
- **THEN** the component SHALL emit an action to its parent
- **AND** it SHALL NOT mutate parent state directly

### Requirement: Focus summary extraction preserves existing behavior
The extracted summary grid SHALL preserve the existing labels, conditional cards, and user-visible actions from the parent panel.

#### Scenario: Conditional summary cards render
- **WHEN** query, stage, dedupe, error type, history, and snapshot focus values are provided
- **THEN** the grid SHALL render the same corresponding summary cards
- **AND** action buttons SHALL remain available for the same focus states
