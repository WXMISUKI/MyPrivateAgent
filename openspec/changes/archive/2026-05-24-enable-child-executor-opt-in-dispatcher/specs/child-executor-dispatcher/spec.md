# child-executor-dispatcher Specification

## Purpose

Define the production-grade opt-in dispatcher boundary that allows child executor work to start only when existing readiness contracts explicitly permit dispatch.

## ADDED Requirements

### Requirement: Dispatcher MUST consume the dispatch contract before starting work

The system MUST require a healthy `child_executor_dispatch_contract` with `dispatch_ready = true` before any real child executor backend is invoked.

#### Scenario: Dispatch contract is blocked

- **WHEN** a caller requests real child executor dispatch
- **AND** `child_executor_dispatch_contract.dispatch_ready = false`
- **THEN** no backend is invoked
- **AND** the dispatch attempt records fail-closed audit evidence

#### Scenario: Dispatch contract is ready

- **WHEN** dispatch is requested
- **AND** promotion gate, execution prerequisites, and backend registry evidence are ready
- **THEN** the dispatcher may invoke the selected backend adapter
- **AND** it records compact dispatch evidence

### Requirement: Dispatcher MUST remain opt-in by default

Default runtime construction MUST keep real child executor dispatch disabled unless an explicitly dispatch-ready backend adapter is configured.

#### Scenario: Default runtime

- **WHEN** the default runtime is built
- **THEN** child executor dispatch remains blocked
- **AND** `will_dispatch` remains false

### Requirement: Dispatcher coverage MUST be machine-readable

Runtime contract smoke, quality gate summary, Runtime Contract Gate, and snapshot guard MUST expose `child_executor_dispatcher_coverage.dispatcher_smoke`.

#### Scenario: Coverage evidence is missing

- **WHEN** a legacy or malformed quality gate report omits dispatcher evidence
- **THEN** `child_executor_dispatcher_coverage.dispatcher_smoke` is false
- **AND** snapshot guard reports the missing field as degraded
