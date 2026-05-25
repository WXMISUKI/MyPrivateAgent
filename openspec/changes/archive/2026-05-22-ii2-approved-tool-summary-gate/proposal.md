# ii2-approved-tool-summary-gate

## Summary

Surface `runtime_approved_tool_execution_bridge` smoke coverage in runtime contract summaries.

## Motivation

The smoke gate now proves approved runtime-service tool execution and deny override fail-closed behavior. However, `runtime_contract_summary` only exposes approval replay coverage. Governance consumers still need to inspect raw checks to know whether the approved tool bridge is covered.

## Scope

- Add `approved_tool_execution_coverage` to `quality_gate_report.py` runtime contract summary.
- Normalize the same field in `RuntimeContractGateService`.
- Include the field in Markdown summary and docs.

## Non-Goals

- Do not change smoke execution behavior.
- Do not add frontend UI in this change.
