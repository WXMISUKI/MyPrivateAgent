## Why

`backend/agent_framework/sdk.py` 已接近 4000 行，恢复协议、child executor、tool runtime bridge、artifact 等多个 concern 混在同一个 Module 中。上一阶段 recovery operation contract 已稳定，适合先抽成独立 Module，提高恢复协议后续演进的 locality。

收口对象：Embedded SDK recovery operation contract 的常量、entrypoint 描述和 operation record builder。

非目标：本变更不改变 SDK 对外 contract shape，不改变恢复语义，不新增 worker lease、不实现跨实例所有权、不改 Runtime Surface read model。

## What Changes

- 新增 `backend/agent_framework/recovery_operations.py`，承接 recovery operation statuses、entrypoints、contract builder 和 operation record builder。
- `backend/agent_framework/sdk.py` 改为通过该 Module 构建 contract 与 operation record。
- 保持现有 SDK recovery operation payload 字段不变。
- 补 focused 测试，确保 refactor 后 SDK contract、probe、Runtime Surface read model 仍保持兼容。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `durable-recovery-operation-contract`: recovery operation contract 的实现应集中在专用 Module，避免 SDK 主类继续承载所有恢复操作构造细节。

## Impact

- Affected code: `backend/agent_framework/sdk.py`、新增 `backend/agent_framework/recovery_operations.py`。
- Affected tests: `tests/agent_framework/test_embedded_runtime_sdk.py`、`tests/agent_framework/test_runtime_surface_service.py`。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`。
- Dependencies: 不新增第三方依赖。
