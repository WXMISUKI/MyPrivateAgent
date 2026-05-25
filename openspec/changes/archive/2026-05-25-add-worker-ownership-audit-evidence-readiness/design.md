## Design

Add `build_worker_ownership_audit_evidence_contract(...)` to `backend/agent_framework/worker_ownership.py`.

The builder is pure/read-only and returns:

- `contract_version`
- `overall_status`
- `ready`
- `authorization_source`
- `evidence`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

The default contract is blocked. It may acknowledge compact ownership evidence but still requires operation history, recovery operation linking, timeline writer evidence, and idempotent dedupe evidence before it can become ready.

`build_worker_ownership_production_gate_contract(...)` accepts `audit_evidence_contract: dict | None`. The `ownership_audit_evidence` section is ready only when the nested audit contract is ready and `authorization_source = false`. This keeps audit evidence descriptive and prevents it from becoming a production execution authorization source.

`build_worker_ownership_operational_readiness_contract(...)` also carries the audit evidence contract for consumers that inspect operational readiness directly.

Runtime smoke, Quality Gate, and Runtime Contract Gate normalize the nested evidence and require it for `worker_ownership_store_mode_coverage.mode_smoke`.

## Compatibility

- Existing callers remain compatible because the new parameters are optional.
- No API endpoint or SDK behavior changes.
- Existing `audit_evidence_ready` boolean remains as a compatibility input used to seed the default nested contract.

## Non-Goals

- Do not implement a durable audit writer.
- Do not make audit evidence an authorization source.
- Do not default-enable worker ownership.
- Do not start background workers or renewal loops.
