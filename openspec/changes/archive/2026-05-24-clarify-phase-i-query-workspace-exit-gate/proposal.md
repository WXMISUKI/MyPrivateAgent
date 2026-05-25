## Why

Phase I now has enough query workspace and channel promotion facts to stop drifting between "continue implementing" and "stay in specs." The project needs an explicit exit/resume gate so future channel work starts from canonical criteria instead of momentum.

## What Changes

- Clarify when Phase I may resume channel-level implementation.
- Clarify when Phase I must remain in architecture/specification mode.
- Add a reusable channel promotion implementation readiness record shape.
- Update roadmap/architecture docs to point future channel work through the gate.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `query-workspace-generalization`: Make Phase I exit criteria explicit and tied to query workspace layers.
- `channel-promotion-gate`: Add implementation readiness recording so channel promotion decisions are canonical.

## Impact

- 收口对象：Phase I exit gate, channel implementation resume criteria, query workspace promotion discipline.
- 受影响后端 contract：无运行时代码变更；后续如实现 channel promotion endpoint 扩展，应按本规格执行。
- 受影响前端消费点：无直接 UI 变更。
- 文档真源：`openspec/specs/query-workspace-generalization/spec.md`, `openspec/specs/channel-promotion-gate/spec.md`, `docs/roadmap/next_phase_hardening.md`, `docs/architecture/runtime_contracts.md`.
- 非目标：不实现新的 `external_adapter` recent summary、不推广 detail/history/workspace、不新增 API 字段、不改现有 tests。
