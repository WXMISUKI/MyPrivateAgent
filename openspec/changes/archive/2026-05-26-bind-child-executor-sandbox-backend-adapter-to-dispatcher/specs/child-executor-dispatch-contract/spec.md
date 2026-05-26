## MODIFIED Requirements

### Requirement: Child executor dispatch contract MUST remain fail-closed before real worker execution
Child executor dispatch contract MUST remain a side-effect-free boundary before any real backend worker execution.

#### Scenario: Sandbox backend binding is required
- **WHEN** the dispatch contract selects a sandbox worker backend
- **THEN** it MUST include `child_executor_sandbox_backend_binding`
- **AND** dispatch readiness MUST require binding readiness in addition to promotion gate, execution prerequisites, backend dispatch readiness, and explicit executor opt-in
- **AND** `will_dispatch` MUST remain false
