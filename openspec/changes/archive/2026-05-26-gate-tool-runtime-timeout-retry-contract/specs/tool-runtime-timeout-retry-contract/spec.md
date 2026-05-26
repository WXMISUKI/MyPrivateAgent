## MODIFIED Requirements

### Requirement: Timeout Retry Boundaries

The system MUST describe timeout/retry posture in the runtime contract and gate the posture through runtime contract quality evidence.

#### Scenario: Runtime contract reports sync adapter posture

- **WHEN** `ToolRuntimeService.build_runtime_contract()` is called
- **THEN** `execution_adapter.timeout_enforcement` MUST identify post-call elapsed checking
- **AND** `execution_adapter.retry_policy` MUST identify synchronous exception retries.

#### Scenario: Runtime contract smoke covers timeout and retry metadata

- **WHEN** runtime contract smoke runs
- **THEN** it MUST include a `tool_runtime_timeout_retry` check
- **AND** the check MUST prove recovered retry metadata, exhausted retry metadata, and post-call elapsed timeout metadata
- **AND** the check MUST NOT claim hard cancellation, sandbox execution, or worker-level timeout enforcement.

#### Scenario: Runtime contract summary guards timeout and retry coverage

- **WHEN** Quality Gate or Runtime Contract Gate summarizes runtime contract checks
- **THEN** it MUST include `runtime_contract_summary.tool_runtime_timeout_retry_coverage.timeout_retry_smoke`
- **AND** malformed or missing timeout/retry evidence MUST fail closed with `timeout_retry_smoke = false`.
