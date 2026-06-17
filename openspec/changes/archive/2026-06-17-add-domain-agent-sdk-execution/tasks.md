## 1. Specification

- [x] 1.1 Create proposal, design, and delta specs.
- [x] 1.2 Validate the OpenSpec change strictly before implementation.

## 2. Core Implementation

- [x] 2.1 Create `backend/domain_agents/weather_assistant/agent.yaml` and `tools.py`.
- [x] 2.2 Create `backend/services/domain_agent_execution_service.py`.
- [x] 2.3 Add `POST /api/agents/{agent_id}/execute` endpoint in `backend/routers/domain_agents.py`.

## 3. Verification

- [x] 3.1 Create `tests/agent_framework/test_domain_agent_execution.py` with deterministic tests.
- [x] 3.2 Run tests in `myenv` (8/8 passed).

## 4. Documentation And Archive

- [x] 4.1 Update runtime contracts and roadmap docs.
- [x] 4.2 Sync canonical specs and archive the completed change.
