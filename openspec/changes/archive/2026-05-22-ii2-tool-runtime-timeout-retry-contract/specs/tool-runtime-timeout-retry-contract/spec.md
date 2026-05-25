## ADDED Requirements

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

The system MUST describe timeout/retry posture in the runtime contract.

#### Scenario: Runtime contract reports sync adapter posture

- **WHEN** `ToolRuntimeService.build_runtime_contract()` is called
- **THEN** `execution_adapter.timeout_enforcement` MUST identify post-call
  elapsed checking
- **AND** `execution_adapter.retry_policy` MUST identify synchronous exception
  retries.
