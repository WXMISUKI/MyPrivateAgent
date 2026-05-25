## MODIFIED Requirements

### Requirement: Dispatcher MUST consume the dispatch contract before starting work

The system MUST require a healthy `child_executor_dispatch_contract` with `dispatch_ready = true` before any real child executor backend is invoked.

When invoking a sandbox worker backend, the dispatcher MUST use the sandbox worker backend adapter contract and MUST reject malformed adapter output.

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

#### Scenario: Sandbox adapter output is malformed

- **WHEN** the selected backend adapter returns non-object output or omits required dispatch attempt evidence
- **THEN** the dispatcher MUST fail closed
- **AND** it MUST record compact error evidence
- **AND** callers MUST NOT treat the child executor as successfully dispatched
