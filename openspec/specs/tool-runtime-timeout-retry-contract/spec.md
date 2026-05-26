# tool-runtime-timeout-retry-contract Specification

## Purpose
Define ToolRuntime timeout and retry posture for synchronous tool execution without overstating cancellation guarantees.
## Requirements
### Requirement: Tool Runtime Retry Metadata

The system MUST expose machine-readable retry metadata from
`ToolRuntimeService.execute_tool(...)`.

#### Scenario: Tool recovers after retry

- **GIVEN** a registered tool fails once and then succeeds
- **WHEN** it is executed with `max_attempts = 2`
- **THEN** the result MUST include `status = ok`
- **AND** `execution.retry.status = recovered`
- **AND** `execution.retry.attempt_count = 2`.

#### Scenario: Tool exhausts retries

- **GIVEN** a registered tool always fails
- **WHEN** it is executed with `max_attempts = 2`
- **THEN** the result MUST include `status = error`
- **AND** `execution.retry.status = exhausted`.

### Requirement: Tool Runtime Timeout Metadata

The system MUST expose machine-readable timeout metadata from
`ToolRuntimeService.execute_tool(...)`.

#### Scenario: Successful call exceeds elapsed timeout

- **GIVEN** a registered tool returns after the configured timeout
- **WHEN** it is executed with `timeout_seconds`
- **THEN** the result MUST include `status = timeout`
- **AND** `execution.timeout.status = exceeded`.

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

