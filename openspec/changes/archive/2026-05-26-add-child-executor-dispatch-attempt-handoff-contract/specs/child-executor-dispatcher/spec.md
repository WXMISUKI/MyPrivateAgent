## ADDED Requirements
### Requirement: Dispatcher Must Keep Attempt Handoff Opt-In
The child executor dispatcher MUST remain disabled by default and MUST treat dispatch attempt handoff readiness as evidence only.

#### Scenario: Handoff ready does not dispatch by itself
- **WHEN** a dispatch attempt handoff contract reports ready
- **THEN** the dispatcher MUST still require explicit enablement and an injected backend adapter
- **AND** default dispatch MUST remain blocked

#### Scenario: Unsafe sandbox payload is guarded
- **WHEN** a sandbox dispatch payload includes unsafe executable handles
- **THEN** the dispatcher or handoff validation MUST report the unsafe payload keys
- **AND** it MUST fail closed before backend adapter invocation
