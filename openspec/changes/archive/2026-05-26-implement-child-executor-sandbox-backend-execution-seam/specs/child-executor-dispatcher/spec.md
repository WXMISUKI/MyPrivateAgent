## MODIFIED Requirements

### Requirement: Dispatcher MUST consume the dispatch contract before starting work
The system MUST require a healthy `child_executor_dispatch_contract` with `dispatch_ready = true` before any real child executor backend is invoked.

When invoking a sandbox worker backend, the dispatcher MUST use the sandbox worker backend adapter contract and MUST reject malformed adapter output.

When sandbox backend binding evidence is present, the dispatcher MUST preserve compact binding evidence in the dispatch attempt and MUST fail closed if the binding evidence is blocked.

#### Scenario: Dispatch contract is blocked
- **WHEN** a caller requests real child executor dispatch
- **AND** `child_executor_dispatch_contract.dispatch_ready = false`
- **THEN** no backend is invoked
- **AND** the dispatch attempt records fail-closed audit evidence

#### Scenario: Dispatch contract is ready
- **WHEN** dispatch is requested
- **AND** promotion gate, execution prerequisites, backend registry evidence, and sandbox backend adapter evidence are ready
- **THEN** the dispatcher may invoke the selected backend adapter
- **AND** it records compact dispatch evidence

#### Scenario: Dispatcher invokes opt-in sandbox execution seam
- **WHEN** dispatch is explicitly enabled
- **AND** dispatch contract, sandbox backend binding, and backend adapter evidence are ready
- **AND** the dispatcher backend adapter is a sandbox backend execution seam
- **THEN** the dispatcher MAY invoke it exactly once for the dispatch request
- **AND** the returned attempt MUST include compact backend result and result handoff evidence
- **AND** it MUST NOT claim parent merge, retry scheduling, or production dispatch authorization

#### Scenario: Sandbox adapter output is malformed
- **WHEN** the selected backend adapter returns non-object output or omits required dispatch attempt evidence
- **THEN** the dispatcher MUST fail closed
- **AND** it MUST record compact error evidence
- **AND** callers MUST NOT treat the child executor as successfully dispatched

#### Scenario: Sandbox backend binding evidence is blocked
- **WHEN** the selected backend is a sandbox worker
- **AND** the dispatch contract carries blocked `child_executor_sandbox_backend_binding` evidence
- **THEN** the dispatcher MUST NOT invoke the backend adapter
- **AND** the attempt MUST include `sandbox_backend_binding_status`, `sandbox_backend_binding_ready`, and `sandbox_backend_binding_missing_sections`
- **AND** callers MUST NOT treat adapter contract readiness as dispatcher binding authorization
