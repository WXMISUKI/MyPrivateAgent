## Overview

这是一刀 dependency promotion。当前 ownership gate 已在 SDK 内部存在，但 default runtime factory 不知道它。我们把 store 放进 `EmbeddedRuntimeDependencies`，让默认 factory、Runtime Surface 和后续 bootstrap 看到同一个依赖边界。

## Module Shape

修改：

- `backend/agent_framework/worker_ownership.py`
  - 新增默认 singleton getter：`get_runtime_worker_ownership_store()`
- `backend/agent_framework/runtime_dependencies.py`
  - `EmbeddedRuntimeDependencies.worker_ownership_store`
  - `get_default_embedded_runtime_dependencies()`
  - `build_runtime_contract().worker_ownership`
- `backend/agent_framework/sdk.py`
  - 当构造参数未显式传入 `worker_ownership_store` 时，从 `runtime_dependencies.worker_ownership_store` 读取。

## Contract Shape

`embedded_runtime_factory.worker_ownership` 至少包含：

- `contract_version`
- `adapter_kind`
- `available`
- `durable`
- `enforcement_mode = opt_in_descriptor_evidence`
- `operations`
- `fail_closed_reasons`

## Semantics

- Default runtime 现在有 in-memory ownership adapter 可用。
- SDK gate 仍只在 persisted descriptor 或 recovery metadata 提供 `worker_ownership` evidence 时触发。
- `recovery_operation_contract.worker_ownership.implemented=false` 默认事实不变，除非具体 operation record 携带 validated ownership evidence。
- `durable=false` 必须清楚表达：这是 dependency seam，不是生产分布式锁。

## Non-Goals

- No SQL lease store.
- No automatic claim/heartbeat.
- No default distributed execution ownership.
- No frontend changes.

## Validation

- Focused tests for dependency bundle and factory contract。
- Existing recovery-focused SDK/Runtime Surface tests。
- OpenSpec strict validation。
