## ADDED Requirements

### Requirement: Runtime contract artifact schema MUST require SDK ToolRuntime bridge coverage

The runtime contract artifact schema MUST list SDK ToolRuntime bridge coverage as a required summary field.

#### Scenario: Artifact summary includes SDK ToolRuntime coverage

- **WHEN** a quality gate report includes runtime contract summary output
- **THEN** the artifact schema check requires `runtime_contract_summary.sdk_tool_runtime_execution_coverage`
- **AND** it requires `runtime_contract_summary.sdk_tool_runtime_execution_coverage.bridge_smoke`
