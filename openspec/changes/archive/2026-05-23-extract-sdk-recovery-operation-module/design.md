## Overview

这是一刀结构治理，不是能力扩展。当前 `sdk.py` 已经成为多个 runtime concern 的聚合点；recovery operation 相关词表和 record builder 已经稳定，适合独立成更深的 Module。

## Module Shape

新增 `backend/agent_framework/recovery_operations.py`：

- `EMBEDDED_SDK_RECOVERY_OPERATION_STATUSES`
- `EMBEDDED_SDK_RECOVERY_OPERATION_ENTRYPOINTS`
- `build_recovery_operation_contract()`
- `recovery_entrypoint_for_continuation_kind(...)`
- `build_recovery_operation_record(...)`

`sdk.py` 保留 orchestration：

- 何时记录 operation。
- 何时把 operation 写入 metadata。
- 何时把 operation 放进 event payload。

`recovery_operations.py` 负责 construction：

- payload 字段归一化。
- worker ownership non-goal。
- compact workspace / continuation refs。

## Compatibility

- `build_embedded_sdk_contract()["recovery_operation_contract"]` 不变。
- `latest_recovery_operation` payload shape 不变。
- `recovery_failed_closed.recovery_operation` payload shape 不变。
- `run_recovery` read model 不变。

## Non-Goals

- 不拆完整 SDK。
- 不改 checkpoint/cursor builder。
- 不新增 Runtime Surface 字段。
- 不删除历史文档或缓存文件。

## Validation

- `tests.agent_framework.test_embedded_runtime_sdk`
- `tests.agent_framework.test_runtime_surface_service`
- `openspec validate --specs --strict`
