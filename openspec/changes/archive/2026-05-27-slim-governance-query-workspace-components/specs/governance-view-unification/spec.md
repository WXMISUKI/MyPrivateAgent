## MODIFIED Requirements

### Requirement: Shared governance interpretation is narrow
The system MUST share only contract interpretation and focus-state derivation between governance views, while keeping local rendering and view state separate. Parent governance panels SHALL keep data loading, route/filter state, and cross-region coordination, while display-only summary regions MAY be extracted into child components when they consume existing contracts without redefining them.

#### Scenario: Shared logic boundary
- **WHEN** Runtime Surface and Governance Timeline reuse helpers
- **THEN** the shared code MUST cover only interpretation and focus derivation
- **AND** the views MUST retain independent rendering and local UI state

#### Scenario: Timeline panel slimming
- **WHEN** the Governance Timeline splits a visual region into a child component
- **THEN** the child component SHALL receive interpreted display data through props
- **AND** it SHALL forward user actions through emits
- **AND** it SHALL NOT redefine backend contract semantics, route behavior, or query/read model interpretation
