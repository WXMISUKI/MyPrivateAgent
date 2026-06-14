## Why

Embedded SDK recovery already has durable workspace, continuation registry, approval, and loop resume pieces, but the evidence is still spread across unit tests, runtime smoke, and contract docs. The next highest-value slice is a deterministic acceptance smoke that tells MyPrivateAgent and future embedded consumers whether the recovery path is safe to consume explicitly.

收口对象：Embedded SDK 的显式恢复消费验收包，覆盖 durable workspace + continuation registry + approval continuation + loop continuation 的最小闭环。

非目标：不实现 worker lease、后台自动恢复、真实 LLM、分布式 executor、默认 `/api/chat` 行为变更、provider invoke、数据库迁移或大规模 SDK 重构。

## What Changes

- Add an `embedded-sdk-recovery-acceptance-smoke-v1` evidence contract with `accepted / blocked` decisions.
- Add a focused service and JSON-only script that run controlled recovery scenarios.
- Treat durable workspace plus required registry bindings as accepted evidence.
- Treat memory-only workspace or missing required registry binding as blocked evidence.
- Ensure smoke evidence excludes callable handlers, provider clients, active streams, and raw executable objects.
- Update runtime architecture and roadmap docs so this acceptance pack is the next Embedded SDK consumption gate.

## Capabilities

### New Capabilities

- `embedded-sdk-recovery-acceptance-smoke`: Defines the deterministic acceptance evidence for explicit Embedded SDK recovery consumption.

### Modified Capabilities

- `embedded-sdk-recovery-protocol`: Adds the requirement that recovery protocol readiness can be verified through the acceptance smoke without enabling automatic recovery.
- `embedded-sdk-continuation-reattachment`: Adds acceptance criteria for registry-backed tool and loop continuation reattachment.
- `embedded-sdk-persistence-interface`: Adds acceptance criteria distinguishing durable workspace acceptance from memory-only blocked posture.
- `durable-recovery-operation-contract`: Adds the requirement that acceptance evidence remains compact and non-executable.

## Impact

- Backend: `backend/agent_framework/*` gains a small acceptance service; `backend/scripts/*` gains a deterministic smoke entrypoint.
- Tests: focused backend tests validate accepted, memory-blocked, registry-blocked, and non-executable evidence behavior.
- Docs: runtime contracts, project entrypoint checklist, and hardening roadmap document the new gate.
- Runtime behavior: no default chat, provider, worker, database schema, or production auto-recovery behavior changes.
