## ADDED Requirements

### Requirement: Reference agent MUST demonstrate the full SDK path with model step and tool execution

The reference agent MUST demonstrate the full SDK path with model step and tool execution.

#### Scenario: Reference agent completes full loop

- **WHEN** the reference agent is executed with a mock provider
- **THEN** the model step generates a response
- **AND** the tool executor executes registered tools
- **AND** the governance trace captures all events
- **AND** the run completes with state `done`

#### Scenario: Reference agent demonstrates tool registration

- **WHEN** tools are registered via `AgentHarnessFacade.register_tool()`
- **AND** the agent is executed
- **THEN** the registered tools are available for execution
- **AND** tool results are recorded in the governance trace

### Requirement: Reference agent MUST be runnable without external dependencies

The reference agent MUST be runnable without external dependencies.

#### Scenario: Reference agent runs with mock tools

- **WHEN** `python examples/weather_sdk_agent.py` is executed
- **THEN** the agent creates a run, registers tools, executes with a model step
- **AND** the agent prints governance evidence
- **AND** the agent exits with code 0
