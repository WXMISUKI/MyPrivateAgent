# child-executor-dispatcher Specification

## Purpose

Define the production-grade opt-in dispatcher boundary that allows child executor work to start only when existing readiness contracts explicitly permit dispatch.

## Requirements

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

### Requirement: Dispatcher MUST remain opt-in by default

Default runtime construction MUST keep real child executor dispatch disabled unless an explicitly dispatch-ready backend adapter is configured.

#### Scenario: Default runtime

- **WHEN** the default runtime is built
- **THEN** child executor dispatch remains blocked
- **AND** `will_dispatch` remains false

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

### Requirement: Dispatcher coverage MUST be machine-readable

Runtime contract smoke, quality gate summary, Runtime Contract Gate, and snapshot guard MUST expose `child_executor_dispatcher_coverage.dispatcher_smoke`.

#### Scenario: Coverage evidence is missing

- **WHEN** a legacy or malformed quality gate report omits dispatcher evidence
- **THEN** `child_executor_dispatcher_coverage.dispatcher_smoke` is false
- **AND** snapshot guard reports the missing field as degraded

### Requirement: Dispatcher MUST attach dispatch result handoff evidence
The child executor dispatcher MUST attach compact result handoff evidence to dispatcher attempts after backend invocation or fail-closed blocking.

#### Scenario: Dispatcher invokes sandbox backend
- **WHEN** the dispatcher invokes a ready sandbox backend adapter
- **THEN** the returned dispatch attempt MUST include `dispatch_result_handoff`
- **AND** the evidence MUST identify whether output and audit references are present
- **AND** it MUST NOT claim parent merge or retry scheduling occurred

#### Scenario: Dispatcher blocks before backend invocation
- **WHEN** the dispatcher blocks due to disabled dispatcher, blocked contract, missing adapter, unsafe payload, adapter exception, or malformed backend result
- **THEN** the returned dispatch attempt MUST include blocked result handoff evidence
- **AND** the evidence MUST preserve the blocked reason in compact form
