## Why

Worker ownership now exposes target decision and input source evidence, but vendor lock semantics still stop at static readiness fields. A side-effect-free adapter seam is needed before production default ownership can safely distinguish "no vendor lock implementation" from "known opt-in adapter that still is not production-authorized".

## What Changes

- Add a vendor lock adapter seam contract for worker ownership.
- Embed the adapter contract into `worker_ownership.vendor_lock_semantics.policy.adapter_contract`.
- Surface adapter contract evidence in `worker_ownership.production_gate.sections[name=vendor_lock_semantics].evidence`.
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate summaries so the missing adapter seam is machine-readable.
- Keep the default posture blocked and descriptive: no real vendor lock backend, no production default ownership, no background worker, and no recovery auto-claim behavior changes.

## Capabilities

### New Capabilities

### Modified Capabilities
- `runtime-worker-ownership-contract`: expose a vendor lock adapter seam contract inside worker ownership vendor lock semantics.
- `worker-ownership-production-gate`: surface vendor lock adapter seam evidence as a production gate blocker.

## Impact

- Affected backend contract: `backend/agent_framework/worker_ownership.py`.
- Affected gate/report paths: `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`, and `backend/services/runtime_contract_gate_service.py`.
- Affected tests: focused worker ownership, runtime smoke, quality gate, and runtime contract gate tests.
- Affected docs/specs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, and worker ownership OpenSpec specs.

收口对象：worker ownership vendor lock adapter seam evidence.

非目标：不实现 MySQL/Postgres/Redis 等真实 vendor lock，不把 SQL row lease/fencing 当成 vendor lock，不启用 production default ownership，不启用 recovery auto-claim，不启动后台续租或 worker。
