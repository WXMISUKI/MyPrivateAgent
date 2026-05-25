## MODIFIED Requirements

### Requirement: Shared governance interpretation is narrow
The system MUST share only contract interpretation and focus-state derivation between governance views, while keeping local rendering and view state separate.

#### Scenario: Shared logic boundary
- **WHEN** Runtime Surface and Governance Timeline reuse helpers
- **THEN** the shared code MUST cover only interpretation and focus derivation
- **AND** the views MUST retain independent rendering and local UI state

#### Scenario: Timeline panel slimming
- **WHEN** Governance Timeline extracts denser UI regions into subcomponents
- **THEN** the shared interpretation contract MUST remain in shared helpers
- **AND** the panel MUST keep orchestration, filtering, and route sync at the top level

### Requirement: Governance entry semantics are unified
The system MUST treat governance entry semantics as a shared contract across Runtime Surface and Governance Timeline.

#### Scenario: Same event, same meaning
- **WHEN** the same runtime event is shown in Runtime Surface and Governance Timeline
- **THEN** both views MUST use the same semantic meaning for the event
- **AND** they MUST NOT invent conflicting labels or interpretations

### Requirement: Snapshot and drill-down actions are consistent
The system MUST keep snapshot focus, query focus, and stage focus semantics consistent across governance views.

#### Scenario: Drill-down parity
- **WHEN** a user drills from summary to detail or from detail to timeline
- **THEN** the target focus MUST behave the same in Runtime Surface and Governance Timeline
- **AND** the same focus action MUST yield the same contract interpretation
