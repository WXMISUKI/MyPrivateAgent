## ADDED Requirements

### Requirement: Domain agents MUST be executable through the SDK path via the API

Domain agents MUST be executable through the SDK path via the API.

#### Scenario: Execute domain agent through API

- **WHEN** `POST /api/agents/{agent_id}/execute` is called with `{"input": "...", "model_name": "..."}`
- **AND** the agent exists in the catalog
- **THEN** the agent is executed through the SDK path
- **AND** the response includes `output`, `events`, and `run`
- **AND** the run state is `done`

#### Scenario: Agent not found returns 404

- **WHEN** `POST /api/agents/{agent_id}/execute` is called with a non-existent agent_id
- **THEN** the response status is 404

### Requirement: Execution service MUST map agent manifests to SDK facade instances

The execution service MUST map agent manifests to SDK facade instances.

#### Scenario: Service creates facade from manifest

- **WHEN** `DomainAgentExecutionService.get_agent("weather_assistant")` is called
- **THEN** an `AgentHarnessFacade` is returned
- **AND** the facade has tools registered from the manifest's `capabilities.tools`
- **AND** the facade's name matches the manifest's `id`

### Requirement: Tool resolution MUST map manifest tool names to executable handlers

Tool resolution MUST map manifest tool names to executable handlers.

#### Scenario: Tool handlers resolved from domain agent module

- **WHEN** the manifest declares `capabilities.tools: ["query_weather", "query_forecast"]`
- **AND** the domain agent has a `tools.py` with matching handler functions
- **THEN** the handlers are registered in the facade
- **AND** the handlers produce valid results when called
