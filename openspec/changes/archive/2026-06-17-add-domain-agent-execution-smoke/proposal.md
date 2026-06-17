# Proposal: Domain Agent Execution End-to-End Smoke Test

## Background

The domain agent SDK execution integration is complete: `DomainAgentExecutionService` maps agent manifests to `AgentHarnessFacade` instances, and `POST /api/agents/{agent_id}/execute` executes domain agents through the SDK path. However, no test validates the full chain: catalog listing → execution → governance trace.

## Purpose

Create an end-to-end smoke test that validates:
1. The weather assistant appears in the domain agent catalog (`/api/agents`)
2. The execution service can create a facade and execute the agent
3. The governance trace is complete (model step, events, state history)
4. Tool execution works through the SDK path

## Scope

- NEW: `tests/agent_framework/test_domain_agent_execution_smoke.py` — end-to-end smoke test
- MODIFIED: Runtime contracts and roadmap docs

## Non-Goals

- No changes to existing code
- No persistence/recovery
- No streaming
- No new domain agents

## Capabilities Affected

- NEW: `domain-agent-execution-smoke`
