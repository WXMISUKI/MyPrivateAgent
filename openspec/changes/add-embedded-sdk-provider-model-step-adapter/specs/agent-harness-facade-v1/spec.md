# agent-harness-facade-v1 (delta)

> Capability: `agent-harness-facade-v1`
> Delta from: `openspec/specs/agent-harness-facade-v1/spec.md`
> Source: `openspec/changes/add-embedded-sdk-provider-model-step-adapter`

## Requirement 1

`AgentHarnessFacade.execute()` MUST accept an optional `model_name` string and auto-build a `model_step` callable from the provider registry when no explicit `model_step` is supplied.

### Scenario: Facade caller supplies model_name string

- **WHEN** `execute(run_id, model_name="doubao")` is called without an explicit `model_step`
- **THEN** the facade builds a `model_step` callable via `build_provider_model_step("doubao")`
- **AND** the built callable is passed to `sdk.execute_run()`
- **AND** model-step metadata and events are produced as if an explicit `model_step` were supplied

### Scenario: Explicit model_step takes precedence over model_name

- **WHEN** `execute(run_id, model_step=my_callable, model_name="doubao")` is called
- **THEN** the explicit `my_callable` is used, not the provider-built one
- **AND** `model_name` is ignored for model_step construction

### Scenario: Neither model_step nor model_name preserves default behavior

- **WHEN** `execute(run_id)` is called without `model_step` or `model_name`
- **THEN** no model_step is passed to `sdk.execute_run()`
- **AND** existing behavior is unchanged
