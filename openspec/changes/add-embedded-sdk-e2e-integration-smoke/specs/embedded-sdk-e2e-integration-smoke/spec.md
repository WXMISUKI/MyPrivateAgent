# embedded-sdk-e2e-integration-smoke

> Capability: `embedded-sdk-e2e-integration-smoke`
> Status: draft
> Source: `openspec/changes/add-embedded-sdk-e2e-integration-smoke`

## Requirement 1

The SDK path MUST complete a full execution loop with model step, tool execution, and governance trace.

### Scenario: Full loop completes with mock provider

- **WHEN** `AgentHarnessFacade.execute()` is called with a `model_step` that returns text and a `tool_executor` that returns a result
- **THEN** the run transitions through `planning → generating → observing → finalizing → done`
- **AND** `metadata.execution_model_step` contains the model output
- **AND** `execution_loop_model_step_completed` event is emitted
- **AND** `execution_loop_done` event is emitted
- **AND** the run state is `done`

### Scenario: Full loop with tool execution

- **WHEN** the model step output triggers a tool call (via tool policy)
- **THEN** the tool executor executes the tool
- **AND** `tool_result` event is emitted
- **AND** the run continues to `finalizing → done`

## Requirement 2

The live smoke test MUST be runnable with a real provider without modifying any source code.

### Scenario: Live smoke test with real provider

- **WHEN** `python backend/scripts/sdk_e2e_smoke.py` is executed with a valid provider configured
- **THEN** the script creates a run, executes it with a real model step, and prints governance evidence
- **AND** the script exits with code 0 on success

## Requirement 3

The integration test MUST be deterministic and runnable in CI.

### Scenario: Deterministic test passes in CI

- **WHEN** `pytest tests/agent_framework/test_sdk_e2e_integration.py` is executed
- **THEN** all tests pass without network access
- **AND** no real LLM calls are made
