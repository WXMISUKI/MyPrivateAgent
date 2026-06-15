# agent-harness-facade-v1 (delta)

> Capability: `agent-harness-facade-v1`
> Delta from: `openspec/specs/agent-harness-facade-v1/spec.md`
> Source: `openspec/changes/add-embedded-sdk-reference-domain-agent`

## Requirement 1

`AgentHarnessFacade` MUST support building a complete domain agent with registered tools and model step.

### Scenario: Facade builds domain agent with tools and model step

- **WHEN** `AgentHarnessFacade(name="weather-agent", model_name="doubao")` is created
- **AND** tools are registered via `register_tool()`
- **AND** `execute(model_name="doubao")` is called
- **THEN** the facade creates a run, executes the full loop, and returns governance evidence
- **AND** the run completes with state `done`
