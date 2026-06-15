# domain-agent-execution-smoke

> Capability: `domain-agent-execution-smoke`
> Status: draft
> Source: `openspec/changes/add-domain-agent-execution-smoke`

## Requirement 1

The domain agent catalog MUST include the weather assistant.

### Scenario: Weather assistant in catalog

- **WHEN** the domain agent catalog is loaded
- **THEN** the catalog includes an entry with `id: weather_assistant`
- **AND** the entry has `capabilities.tools` containing `query_weather` and `query_forecast`

## Requirement 2

The execution service MUST execute the full chain end-to-end.

### Scenario: Full chain execution

- **WHEN** `DomainAgentExecutionService.execute("weather_assistant", ...)` is called with a mock provider
- **THEN** the execution returns `ok: true`
- **AND** `output` contains model-generated text
- **AND** `events` includes `execution_loop_model_step_completed` and `execution_loop_done`
- **AND** `run.state` is `done`
- **AND** `run.state_history` covers `generating → done`
