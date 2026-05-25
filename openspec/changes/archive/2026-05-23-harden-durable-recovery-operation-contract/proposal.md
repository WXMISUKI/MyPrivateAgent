## Why

Embedded SDK 已经具备 durable workspace posture、checkpoint、resume cursor 和 registry reattachment，但实际恢复入口缺少“本次恢复操作”的统一审计包络。企业生产级 Agent 平台需要能回答：谁在什么时候尝试从哪个入口恢复、恢复是否被 durable/registry/approval gate 阻断、成功恢复是否来自持久化 descriptor，而不是只从事件流和 metadata 反推。

收口对象：Embedded SDK durable recovery operation contract，覆盖 `submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 两个恢复入口的操作级证据。

非目标：本变更不引入 worker lease、跨实例锁、远程 executor、sandbox、hard timeout、多租户权限模型或完整分布式调度所有权。

## What Changes

- 新增 recovery operation contract，用机器可读字段描述恢复尝试 id、entrypoint、status、reason、checkpoint/cursor refs、workspace evidence 和 worker ownership boundary。
- 在 SDK 成功通过 persisted descriptor + registry reattachment 恢复时记录 `recovered` 操作证据。
- 在 SDK 恢复被 fail-closed 阻断时记录 `blocked` 操作证据，并把该证据放入 `recovery_failed_closed` 事件和 run metadata。
- 在 `probe_run_recovery()` 结果中暴露当前 operation boundary，说明哪些入口可审计、哪些生产能力仍未实现。
- 更新架构文档与 focused SDK tests，确保该契约不会复制 callable、provider client、stream iterator 或任意 executable internals。

## Capabilities

### New Capabilities

- `durable-recovery-operation-contract`: 定义 Embedded SDK 恢复操作级审计包络、状态枚举、入口范围和 worker ownership 非目标边界。

### Modified Capabilities

- `embedded-sdk-recovery-protocol`: 恢复协议需要在 probe、成功恢复和 fail-closed 恢复事件中暴露 recovery operation evidence。

## Impact

- Affected backend contract: `backend/agent_framework/sdk.py` 的 Embedded SDK contract、probe result、recovery success/fail-closed metadata/event payload。
- Affected frontend consumption points: Runtime Surface / Governance Timeline 仍优先消费后端 recovery/read model；本切片不直接改前端，但为后续展示 operation evidence 提供后端事实源。
- Docs truth sources: `docs/architecture/runtime_contracts.md`、`docs/architecture/current_architecture.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
- Dependencies: 不新增第三方依赖。
