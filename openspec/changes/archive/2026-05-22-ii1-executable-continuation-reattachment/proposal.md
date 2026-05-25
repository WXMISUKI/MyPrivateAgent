## Why

II-1.3 已经把 recovery probe、fail-closed gate 和 machine-readable recovery result 建起来了，但当前系统仍然只能在“当前进程里还有 executable continuation”时恢复。

这意味着：

- persisted continuation descriptor 已可观测
- recovery reason 已可解释
- 但只要进程切换，系统仍只能停在 `missing_executable_continuation`

如果继续直接做 durable backend 默认化、child executor 或多实例协调，这个缺口会被不断放大。下一步更合理的是先补一个正式的 executable continuation reattachment seam，让恢复能力从“只会判断”推进到“在明确绑定存在时可以重新挂接执行能力”。

## What Changes

- 为 Embedded SDK 增加 continuation registry / resolver seam
- 让 tool continuation 与 loop continuation descriptor 可以持久化 binding identity，而不只持久化状态摘要
- 让 `probe_run_recovery()` 在 binding 可解析时把 continuation 判定为 recoverable
- 让 `submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 在 registry 可解析时完成 reattach，而不是直接 fail-closed
- 在 registry 缺失或 binding 不存在时，继续标准化返回 fail-closed，并暴露新的 recovery reason

## Impact

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/continuations.py`
- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

