## ADDED Requirements

### Requirement: Execution loop MUST support an opt-in model step

The Embedded SDK execution loop MUST support an explicit `model_step` callable during the `generating` stage without changing default execution behavior.

#### Scenario: Model step completes successfully

- **WHEN** a caller executes a run with `model_step`
- **THEN** the loop MUST call it during the `generating` stage
- **AND** the run metadata MUST include compact `execution_model_step` evidence
- **AND** the event stream MUST include `execution_loop_model_step_completed`
- **AND** the run MUST continue to later loop stages unless another gate stops it

#### Scenario: No model step keeps existing behavior

- **WHEN** a caller executes a run without `model_step`
- **THEN** existing loop behavior MUST remain unchanged
- **AND** no model-step metadata or event MUST be emitted

### Requirement: Model step evidence MUST be compact and non-executable

Model-step output MUST be normalized into compact evidence and MUST NOT expose executable or provider runtime objects.

#### Scenario: Unsafe model output fields are excluded

- **WHEN** `model_step` returns output containing callables, provider clients, stream iterators, or raw SDK objects
- **THEN** those fields MUST be excluded or sanitized
- **AND** compact fields such as `text`, `summary`, `model_name`, `finish_reason`, `usage`, and safe metadata MAY be retained

### Requirement: Model step failure MUST reuse loop fallback semantics

Model-step exceptions MUST use the existing execution-loop fallback/fail-closed path.

#### Scenario: Fallback handles model step failure

- **WHEN** `model_step` raises an exception
- **AND** the fallback handler returns `status = handled`
- **THEN** the loop MUST emit `execution_loop_fallback_applied`
- **AND** the run MAY continue to later loop stages

#### Scenario: Unhandled model step failure fails closed

- **WHEN** `model_step` raises an exception
- **AND** fallback does not handle it
- **THEN** the loop MUST emit `execution_loop_failed`
- **AND** the run MUST transition to `failed` with `stop_reason = loop_exception`

### Requirement: Model step MUST remain an explicit SDK consumption seam

The model-step contract MUST remain opt-in and MUST NOT imply real model provider execution.

#### Scenario: Contract boundary is inspected

- **WHEN** a consumer reads the model-step contract or emitted evidence
- **THEN** it MUST be clear that no real LLM provider, streaming, default chat routing, worker execution, or provider promotion is implied
