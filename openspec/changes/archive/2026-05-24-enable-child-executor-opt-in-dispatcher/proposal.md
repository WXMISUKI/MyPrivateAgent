# enable-child-executor-opt-in-dispatcher

## Why

The platform currently has child executor preflight, promotion gate, prerequisites, backend registry, and dispatch contract. The remaining production step is an opt-in dispatcher that can execute through a registered backend only after all existing readiness contracts allow it.

## What Changes

- Add an opt-in child executor dispatcher contract and backend adapter seam.
- Require dispatcher calls to consume `child_executor_dispatch_contract` before starting work.
- Keep default runtime behavior blocked until an explicitly dispatch-ready backend is configured.
- Add smoke/quality gate evidence for the opt-in dispatcher path.

## Impact

- 收口对象：backend child executor dispatcher service/adapter, SDK/facade delegate path, runtime contract smoke, quality gate docs/specs.
- 非目标：不把 existing relationship seam 默认为真实 execution；不绕过 promotion gate/prerequisites/backend registry。
