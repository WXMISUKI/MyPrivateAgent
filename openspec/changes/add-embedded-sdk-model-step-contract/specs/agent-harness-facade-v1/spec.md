## ADDED Requirements

### Requirement: Agent harness facade MUST pass explicit model step to SDK execution

`AgentHarnessFacade.execute(...)` MUST accept an explicit `model_step` callable and pass it to `EmbeddedAgentRuntimeSDK.execute_run(...)`.

#### Scenario: Facade caller supplies model step

- **WHEN** a facade caller invokes `execute(..., model_step=...)`
- **THEN** the embedded SDK execution loop MUST receive that callable
- **AND** model-step metadata and events MUST be produced by the SDK-owned loop
- **AND** facade default behavior MUST remain unchanged when no model step is supplied
