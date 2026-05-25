## Why

II-1.4 已经把 continuation reattach 从“只能 fail-closed”推进到“在 registry 可解析 binding 时可以恢复”。但当前 binding 仍主要依赖调用方手工约定字符串，缺少标准化目录与元数据。

这会带来几个问题：

- 调用方不知道当前 registry 到底暴露了哪些 continuation binding
- probe 虽然能判断能不能恢复，但不能回答“缺的是哪类 binding、属于哪个能力面”
- 后续 child executor、worker process 和运维排障缺少统一的 binding 清单真源

因此，下一步需要把 continuation binding 从“字符串约定”推进成“有标准 catalog/manifest 的能力面”。

## What Changes

- 为 `EmbeddedContinuationRegistry` 增加标准 binding metadata 和 catalog 输出能力
- 让 `InMemoryEmbeddedContinuationRegistry` 在注册时记录 `binding_kind / handler_name / metadata`
- 为 `EmbeddedAgentRuntimeSDK` 增加查询 continuation binding catalog 的窄接口
- 让 recovery probe 结果可引用 binding catalog 信息，便于排障和后续执行器前置校验

## Impact

- `backend/agent_framework/continuation_registry.py`
- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

