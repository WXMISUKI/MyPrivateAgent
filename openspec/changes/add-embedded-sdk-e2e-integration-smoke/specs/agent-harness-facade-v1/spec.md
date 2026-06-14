# agent-harness-facade-v1 (delta)

> Capability: `agent-harness-facade-v1`
> Delta from: `openspec/specs/agent-harness-facade-v1/spec.md`
> Source: `openspec/changes/add-embedded-sdk-e2e-integration-smoke`

## Requirement 1

`AgentHarnessFacade` MUST support a complete end-to-end execution with model step and tool execution.

### Scenario: Facade completes full loop with registered tool

- **WHEN** a tool is registered via `facade.register_tool(spec, handler)`
- **AND** `facade.execute(run_id, model_step=my_model_step)` is called
- **AND** the model step output triggers the registered tool
- **THEN** the tool handler is invoked
- **AND** the tool result is recorded in `run.tool_history`
- **AND** the run completes with state `done`
