# Runtime Surface Regression Hardening

## Why

上一轮 focused 验证通过后，扩大运行 `tests.agent_framework.test_runtime_surface_service` 暴露出 4 个 Runtime Surface 既有回归：SDK reader factory 未被调用、embedded bootstrap update 遇到 mock contract 报错、child executor replay 状态从预期 `executed` 退化为 `blocked`。这些问题会降低 Runtime Surface 作为控制面真源的可信度，需要独立修复，避免后续垂域 agent registry 或治理台工作建立在不稳定 profile 上。

## What Changes

- 修复 Runtime Surface 对 runtime factory、bootstrap recovery validation、child executor replay/read model 的回归。
- 用既有 `test_runtime_surface_service` 中的失败用例作为回归保护。
- 若涉及契约说明，更新 `docs/architecture/runtime_contracts.md` 或 roadmap 中的相关说明。

## Non-goals

- 不改变 domain agent registry 的 contract。
- 不新增外部 framework adapter。
- 不重构 Runtime Surface 大型 assembler。
- 不修改前端治理台 UI。
- 不处理无关的 pytest cache 权限目录。

## Impact

- Backend: `backend/services/runtime_surface_service.py` 及必要的相邻 service/read model。
- Tests: `tests/agent_framework/test_runtime_surface_service.py` 相关失败用例必须转绿。
- Docs/spec: 若修复澄清了 contract 行为，需要同步运行时契约文档。
