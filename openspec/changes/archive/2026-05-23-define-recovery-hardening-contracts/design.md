## Overview

本变更只定义后续硬化规格，不实现代码。三类能力按依赖顺序设计：

1. `runtime-worker-ownership-contract`：先定义谁有权恢复或继续执行某个 run。
2. `recovery-retry-protocol`：在 ownership 与 operation evidence 基础上定义失败重试。
3. `recovery-audit-hardening`：把 ownership / retry / operation evidence 汇总成治理可读的审计面。

## Shared Principles

- Existing recovery operation evidence remains the base event envelope.
- Worker ownership MUST NOT be inferred from process-local maps.
- Retry MUST be idempotent and bounded.
- Audit hardening MUST be compact and non-executable.
- Runtime Surface remains the read-side entry for governance consumers.

## Dependency Direction

`recovery-audit-hardening` may consume:

- `durable-recovery-operation-contract`
- `runtime-surface-recovery-operation-read-model`
- `runtime-worker-ownership-contract`
- `recovery-retry-protocol`

`recovery-retry-protocol` may consume:

- `runtime-worker-ownership-contract`
- `durable-recovery-operation-contract`

`runtime-worker-ownership-contract` should stand alone as the first production hardening seam.

## Non-Goals

- No schema migration in this change.
- No worker execution implementation.
- No queue, scheduler, or distributed lock adapter.
- No UI work.
- No archiving into canonical specs unless the team decides these future specs are accepted.

## Suggested Implementation Order

1. Implement worker ownership read/write contract and in-memory/sql adapter shape.
2. Add recovery retry state machine using operation evidence and ownership fencing.
3. Add Runtime Surface audit summary and contract smoke coverage.
