## 1. Specification

- [x] 1.1 Create proposal, design, and delta specs for the provider model-step adapter.
- [x] 1.2 Validate the OpenSpec change strictly before implementation.

## 2. Core Implementation

- [x] 2.1 Create `build_provider_model_step()` factory function in `backend/agent_framework/provider_model_step.py`.
- [x] 2.2 Add facade convenience: `AgentHarnessFacade.execute()` accepts `model_name` string and auto-builds model_step.

## 3. Verification

- [x] 3.1 Add focused backend tests for provider resolution, successful call, provider unavailable, and response normalization.
- [x] 3.2 Run focused tests and OpenSpec validation.

## 4. Documentation And Archive

- [x] 4.1 Update runtime contracts and roadmap docs with the provider model-step adapter boundary.
- [x] 4.2 Sync canonical specs and archive the completed change.
