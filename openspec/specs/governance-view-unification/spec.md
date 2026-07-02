# governance-view-unification Specification

## Purpose
Unify governance view domain, filter, and navigation semantics across Runtime Surface and Governance Timeline.
## Requirements
### Requirement: Governance entry semantics are unified
The system MUST treat governance entry semantics as a shared contract across Runtime Surface and Governance Timeline.

#### Scenario: Same event, same meaning
- **WHEN** the same runtime event is shown in Runtime Surface and Governance Timeline
- **THEN** both views MUST use the same semantic meaning for the event
- **AND** they MUST NOT invent conflicting labels or interpretations

### Requirement: Route focus is standardized
The system MUST treat governance route state as a standardized observation focus model for filtering and drill-down.

#### Scenario: Route-driven focus
- **WHEN** a user changes governance route focus
- **THEN** the system MUST interpret the route as an observation focus
- **AND** it MUST NOT treat route values as durable runtime object definitions

### Requirement: Snapshot and drill-down actions are consistent
The system MUST keep snapshot focus, query focus, and stage focus semantics consistent across governance views.

#### Scenario: Drill-down parity
- **WHEN** a user drills from summary to detail or from detail to timeline
- **THEN** the target focus MUST behave the same in Runtime Surface and Governance Timeline
- **AND** the same focus action MUST yield the same contract interpretation

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

### Requirement: Non-main_chat expansion is explicit
The system MUST treat any expansion of governance view semantics beyond the current `main_chat`-driven workflow as a separately evaluated decision.

#### Scenario: New channel evaluation
- **WHEN** a future governance channel is considered for unification
- **THEN** the system MUST evaluate it separately
- **AND** it MUST NOT assume it automatically inherits the current `main_chat` semantics

### Requirement: Runtime Surface governance view MAY render provider ops posture
The Runtime Surface governance view SHALL be able to render provider ops posture as a compact diagnostic card.

#### Scenario: Provider ops renders in Runtime Surface
- **WHEN** the frontend Runtime Surface panel consumes a profile with `provider_ops`
- **THEN** it may render summary counts and compact per-provider posture fields
- **AND** it remains diagnostic-only

#### Scenario: Empty provider ops is visible
- **WHEN** provider ops data is empty or degraded
- **THEN** the Runtime Surface panel shows a stable empty or degraded state
- **AND** it does not silently hide the governance area

