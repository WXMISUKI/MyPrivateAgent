## MODIFIED Requirements

### Requirement: Child executor dispatcher MUST remain opt-in and fail-closed
The child executor dispatcher MUST remain disabled by default and MUST fail closed unless explicit dispatch readiness and backend adapter evidence are present.

#### Scenario: Dispatcher preserves sandbox backend binding evidence
- **WHEN** the dispatcher receives `child_executor_sandbox_backend_binding` in the dispatch contract
- **THEN** every dispatch attempt MUST preserve compact binding status, readiness, and missing section evidence
- **AND** the dispatcher MUST NOT execute binding builder side effects
- **AND** default disabled dispatcher attempts MUST remain blocked
