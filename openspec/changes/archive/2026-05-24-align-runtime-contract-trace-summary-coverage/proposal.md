# align-runtime-contract-trace-summary-coverage

## Why

Runtime Contract Gate summaries already normalize many smoke coverage fields, and Governance Timeline compact summaries can display them. The Health Router trace writer currently preserves only a subset of those coverage sections in `runtime_contract_gate_degraded.payload.runtime_contract_summary`, so persisted governance traces can lose SDK tool, embedded persistence, worker ownership, and child executor gate/prerequisite/dispatch evidence.

## What Changes

- Normalize the remaining runtime contract summary coverage sections before writing degraded governance traces.
- Add compact detail labels for SDK tool, embedded persistence, worker ownership, child executor gate, prerequisites, dispatch, and subagent detail.
- Add focused backend tests for payload preservation and detail labels.

## Impact

- 收口对象：`backend/routers/health.py`, `tests/agent_framework/test_health_router.py`, docs/specs.
- 非目标：不改变 `quality_gate_report.py`、Runtime Contract Gate derivation、snapshot guard 或任何 runtime execution behavior。
