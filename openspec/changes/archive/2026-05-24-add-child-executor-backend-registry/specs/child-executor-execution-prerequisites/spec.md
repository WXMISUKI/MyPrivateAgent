## ADDED Requirements

### Requirement: Execution Prerequisites Must Include Backend Registry Evidence
Child executor execution prerequisites MUST include backend registry evidence when reporting worker backend readiness.

#### Scenario: Worker backend blocks execution
- **WHEN** worker backend readiness is blocked by the backend registry
- **THEN** execution prerequisites MUST include the worker backend requirement in `missing_requirements`
- **AND** the requirement evidence MUST include the registry backend status and blockers
- **AND** readiness MUST remain false
