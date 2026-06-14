# embedded-sdk-provider-model-step-adapter

> Capability: `embedded-sdk-provider-model-step-adapter`
> Status: draft
> Source: `openspec/changes/add-embedded-sdk-provider-model-step-adapter`

## Requirement 1

`build_provider_model_step()` MUST return a valid `ModelStepCallable` that resolves a model from the provider registry and invokes it.

### Scenario: Provider resolves model and returns ExecutionModelStepResult

- **WHEN** `build_provider_model_step(model_name="doubao")` is called
- **THEN** a callable is returned
- **WHEN** the callable is invoked with an `AgentRunContext` whose `model_name` is `"doubao"`
- **AND** the provider registry has a backend that supports `"doubao"`
- **THEN** the backend's model is invoked with a message constructed from the run context
- **AND** the result is an `ExecutionModelStepResult` (or dict) with `text`, `model_name`, and `finish_reason` fields

### Scenario: Provider not available raises exception

- **WHEN** `build_provider_model_step(model_name="nonexistent")` is called
- **THEN** a callable is returned
- **WHEN** the callable is invoked with an `AgentRunContext`
- **AND** no backend supports `"nonexistent"`
- **THEN** the callable raises an exception
- **AND** the execution loop routes the exception through the existing fallback/fail-closed path

## Requirement 2

The adapter MUST construct messages from the run context without requiring external message history.

### Scenario: Messages constructed from run context metadata

- **WHEN** the callable is invoked with an `AgentRunContext`
- **THEN** it constructs messages from `run_context.metadata.get("system_prompt")` (if present) and `run_context.metadata.get("user_message")` or `run_context.metadata.get("input")`
- **AND** the constructed messages are passed to the model's `invoke()` method

## Requirement 3

The adapter MUST be opt-in and MUST NOT change default behavior.

### Scenario: Adapter is not used by default

- **WHEN** `execute_run()` is called without a `model_step` parameter
- **THEN** no provider model-step adapter is invoked
- **AND** existing behavior is unchanged

## Requirement 4

The adapter MUST NOT expose unsafe provider objects in the result.

### Scenario: Model instance and API client excluded from result

- **WHEN** the callable returns a result
- **THEN** the result contains only safe fields (text, summary, model_name, finish_reason, usage, metadata)
- **AND** the result does not contain model instances, API clients, or callable references
