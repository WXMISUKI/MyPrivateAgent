## ADDED Requirements

### Requirement: Runtime contract smoke MUST cover SDK direct ToolRuntime execution

The runtime contract smoke gate MUST include a machine-readable check for `EmbeddedAgentRuntimeSDK` using `ToolRuntimeService` directly.

#### Scenario: SDK direct ToolRuntime bridge is covered

- **GIVEN** an SDK instance configured with `ToolRuntimeService`
- **AND** tools registered through `sdk.register_tool(...)`
- **WHEN** `runtime_contract_smoke.py` runs
- **THEN** the output includes a check named `sdk_tool_runtime_execution_bridge`
- **AND** the check proves auto permission execution calls the handler once
- **AND** the check proves ask permission enters approval and executes once after approval
- **AND** the check proves deny permission does not call the handler

### Requirement: Quality gate summary MUST expose SDK ToolRuntime bridge coverage

Quality gate summary consumers MUST be able to determine SDK ToolRuntime bridge coverage without scanning raw smoke checks.

#### Scenario: SDK bridge coverage is normalized

- **GIVEN** the smoke output includes `sdk_tool_runtime_execution_bridge`
- **WHEN** `quality_gate_report.py` or `RuntimeContractGateService` builds `runtime_contract_summary`
- **THEN** `runtime_contract_summary.sdk_tool_runtime_execution_coverage.bridge_smoke` is true only when evidence fields match the expected SDK bridge behavior
- **AND** missing, failed, or malformed evidence produces `bridge_smoke = false`
