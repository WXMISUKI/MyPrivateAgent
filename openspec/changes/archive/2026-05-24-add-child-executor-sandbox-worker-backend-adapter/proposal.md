## Why

Child executor has reached the observability and gate boundary: preflight, promotion gate, execution prerequisites, backend registry, dispatch contract, and opt-in dispatcher all exist. The next maturity step is to define a real sandbox worker backend adapter contract before any implementation can safely flip `dispatch_ready` from false to true.

## What Changes

- Introduce a `child-executor-sandbox-worker-backend` capability that defines the worker backend adapter contract, execution envelope, sandbox constraints, audit evidence, and fail-closed behavior.
- Extend backend registry requirements so a sandbox backend can become dispatch-ready only when its adapter contract, sandbox limits, and audit hooks are present.
- Extend dispatch contract requirements so `dispatch_ready=true` requires a selected backend that is sandbox-ready and opt-in enabled.
- Extend dispatcher requirements so backend invocation uses a stable adapter interface and records compact dispatch evidence.

## Capabilities

### New Capabilities

- `child-executor-sandbox-worker-backend`: Defines the sandbox worker backend adapter contract for real child executor dispatch.

### Modified Capabilities

- `child-executor-backend-registry`: Add sandbox-ready backend evidence and stricter dispatch readiness requirements.
- `child-executor-dispatch-contract`: Require sandbox backend evidence before dispatch readiness can become true.
- `child-executor-dispatcher`: Require dispatcher invocation to use the sandbox backend adapter contract and fail closed on malformed adapter output.

## Impact

- 收口对象：真实 child executor dispatch 前的 sandbox worker backend adapter 规格。
- 受影响后端 contract：`child_executor_backend_registry`, `child_executor_dispatch_contract`, `ChildExecutorDispatcher` adapter interface.
- 受影响前端消费点：无直接 UI 变更；后续前端仍只消费 `dispatch_ready / will_dispatch / blockers` 等 compact evidence。
- 文档真源：`openspec/specs/child-executor-*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不启动真实 worker、不实现 sandbox runtime、不接 queue、不改变默认 `dispatch_ready=false`、不把 promotion gate passed 直接等同于可执行。
