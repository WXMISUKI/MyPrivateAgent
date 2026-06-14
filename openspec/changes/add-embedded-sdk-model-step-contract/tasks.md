## 1. Specification

- [x] 1.1 Create proposal, design, and delta specs for the Embedded SDK model-step contract.
- [x] 1.2 Validate the OpenSpec change strictly before implementation.

## 2. Core Implementation

- [ ] 2.1 Add normalized `ExecutionModelStepResult` and `model_step` callable support to `ExecutionLoopController`.
- [ ] 2.2 Emit compact `execution_loop_model_step_completed` evidence and route exceptions through existing fallback/fail-closed behavior.
- [ ] 2.3 Pass explicit `model_step` through `EmbeddedAgentRuntimeSDK.execute_run(...)` and `AgentHarnessFacade.execute(...)`.

## 3. Verification

- [ ] 3.1 Add focused backend tests for model-step success, reviewer consumption, handled fallback, fail-closed failure, and sanitization.
- [ ] 3.2 Run focused tests and OpenSpec validation.

## 4. Documentation And Archive

- [ ] 4.1 Update runtime contracts and next-phase roadmap docs with the model-step boundary.
- [ ] 4.2 Sync canonical specs and archive the completed change.
