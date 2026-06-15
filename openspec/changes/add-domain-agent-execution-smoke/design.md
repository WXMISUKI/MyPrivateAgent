# Design: Domain Agent Execution End-to-End Smoke Test

## Context

The domain agent SDK execution integration is complete. The `DomainAgentExecutionService` maps agent manifests to `AgentHarnessFacade` instances. The `POST /api/agents/{agent_id}/execute` endpoint executes domain agents through the SDK path. But no test validates the full chain end-to-end.

## Goals

1. Validate that the weather assistant appears in the domain agent catalog.
2. Validate that the execution service can create a facade and execute the agent.
3. Validate that the governance trace is complete.
4. Validate that tool execution works through the SDK path.

## Non-Goals

1. No changes to existing code.
2. No persistence/recovery.
3. No streaming.
4. No new domain agents.

## Key Decisions

### Decision 1: Deterministic tests with mock provider

The smoke tests use mock providers (no real LLM calls). This makes them:
- Deterministic (always pass)
- Fast (no network latency)
- CI-friendly (no external dependencies)

### Decision 2: Test the full chain, not just the service

The tests validate:
1. Catalog listing includes weather_assistant
2. Execution service creates facade with registered tools
3. Execute returns ok, output, events, run
4. Governance trace includes model_step_completed and done events
5. State history covers the full loop

### Decision 3: Separate from existing domain_agent_execution tests

The existing `test_domain_agent_execution.py` tests the service in isolation. The new smoke test validates the full chain including catalog integration.

## Risks

| Risk | Mitigation |
|------|-----------|
| Catalog may not include weather_assistant | Test validates it does |
| Tools may not be resolved correctly | Test validates tool registration |

## Migration

None required. This adds tests only.
