## Why

Worker ownership rollout confirmation already has a decision record, but the contract does not yet identify the operational source of that decision. This makes it hard for runtime smoke and quality gates to distinguish a missing rollout confirmation source from a recorded but still blocked rollout decision.

## What Changes

- Add a read-only rollout confirmation input source contract for worker ownership production rollout.
- Embed that source under `worker_ownership.production_rollout.operationalization.confirmation_decision.input_source`.
- Surface the same source evidence in `worker_ownership.production_gate.sections[name=rollout_checklist].evidence`.
- Extend runtime smoke, Quality Gate, Runtime Contract Gate, docs, and canonical specs so blocked rollout remains machine-readable.
- Keep production recovery, default worker ownership, auto-claim, background supervisor, and vendor lock adapter behavior unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities
- `runtime-worker-ownership-contract`: expose rollout confirmation input source evidence as part of worker ownership runtime contracts.
- `worker-ownership-production-gate`: surface rollout confirmation input source blockers in the production gate rollout checklist.

## Impact

- Affected backend contract: `backend/agent_framework/worker_ownership.py`.
- Affected gate/report paths: `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`, and `backend/services/runtime_contract_gate_service.py`.
- Affected tests: focused worker ownership, runtime smoke, quality gate, and runtime contract gate tests.
- Affected docs/specs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, and the runtime worker ownership OpenSpec specs.

收口对象：worker ownership production rollout confirmation input source evidence.

非目标：不实现真实 rollout、不启用 production default ownership、不启用 recovery entry auto-claim、不实现 vendor-specific lock adapter、不启动后台 worker 或 renewal supervisor。
