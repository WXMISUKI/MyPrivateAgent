## MODIFIED Requirements

### Requirement: Shared governance interpretation is narrow
The system MUST share only contract interpretation and focus-state derivation between governance views, while keeping local rendering and view state separate.

#### Scenario: Shared logic boundary
- **WHEN** Runtime Surface and Governance Timeline reuse helpers
- **THEN** the shared code MUST cover only interpretation and focus derivation
- **AND** the views MUST retain independent rendering and local UI state
- **AND** the shared interpretation path MUST preserve query read model metadata such as layer, source channel, and identity kind when those contracts are rendered

### Requirement: Governance entry semantics are unified
The system MUST treat governance entry semantics as a shared contract across Runtime Surface and Governance Timeline.

#### Scenario: Same event, same meaning
- **WHEN** the same runtime event is shown in Runtime Surface and Governance Timeline
- **THEN** both views MUST use the same semantic meaning for the event
- **AND** they MUST NOT invent conflicting labels or interpretations
- **AND** they MUST preserve the same metadata visibility semantics for `main_chat_query_detail` and `main_chat_query_history`

### Requirement: Snapshot and drill-down actions are consistent
The system MUST keep snapshot focus, query focus, and stage focus semantics consistent across governance views.

#### Scenario: Drill-down parity
- **WHEN** a user drills from summary to detail or from detail to timeline
- **THEN** the target focus MUST behave the same in Runtime Surface and Governance Timeline
- **AND** the same focus action MUST yield the same contract interpretation
- **AND** the rendered detail/history views MUST remain layout-compatible while still surfacing query read model metadata
