# approved-tool-summary-gate Specification

## Purpose
Ensure approved tool execution coverage is summarized by the runtime contract gate so consumers can detect whether approval replay paths are covered.
## Requirements
### Requirement: Quality gate summary MUST expose approved tool bridge coverage

`quality_gate_report.py` MUST derive `approved_tool_execution_coverage` from the `runtime_approved_tool_execution_bridge` smoke check.

#### Scenario: Summary reports approved tool bridge covered

- **WHEN** runtime contract checks include a passing `runtime_approved_tool_execution_bridge`
- **THEN** `runtime_contract_summary.approved_tool_execution_coverage.bridge_smoke` is `true`
- **AND** approved and deny override fields are preserved in compact form

### Requirement: Runtime contract gate MUST normalize approved tool bridge coverage

`RuntimeContractGateService` MUST expose normalized `approved_tool_execution_coverage` in `runtime_contract_summary`.

#### Scenario: Missing approved tool bridge check is uncovered

- **WHEN** contract checks do not include `runtime_approved_tool_execution_bridge`
- **THEN** `runtime_contract_summary.approved_tool_execution_coverage.bridge_smoke` is `false`

### Requirement: Markdown summary MUST show approved tool bridge coverage

The quality gate Markdown Runtime Contract Summary table MUST show whether approved tool bridge coverage is present.

#### Scenario: Markdown table includes approved tool bridge column

- **WHEN** `runtime_contract_summary.approved_tool_execution_coverage.bridge_smoke` is true
- **THEN** the Markdown Runtime Contract Summary row contains `yes` in the approved tool bridge column
