# Agent Runtime Control Plane Entrypoint

> Start here. This page is the current entrypoint for understanding MyPrivateAgent without reading historical change logs first.

## Current Position

MyPrivateAgent is an enterprise Agent Runtime Control Plane. It is not a replacement implementation of LangGraph, CrewAI, Qwen-Agent, OpenAI Agents SDK, DeerFlow, Agno, or similar frameworks.

The project owns:

- Runtime Core objects: run, event, approval, artifact, trace, audit, memory, skill, tool.
- Capability contracts: ToolRuntime, MCP, Skill, MemoryOps, PromptOps, external provider adapters.
- Governance contracts: runtime contract gate, policy, approval, timeline, doctor, health, quality gate evidence.
- Delivery surfaces: FastAPI service APIs, Runtime Surface, Governance Timeline, Embedded SDK, Agent Harness Facade.

External frameworks and provider projects are execution or data-plane candidates. They must integrate through adapters or provider contracts and cannot become the primary frontend/governance contract.

## Layer Map

| Layer | Owns | Main entry |
|---|---|---|
| Runtime Core | run/event/state/approval/artifact semantics | [current_architecture.md](./current_architecture.md) |
| Capability Layer | tool, MCP, skill, memory, command, provider contracts | [runtime_contracts.md](./runtime_contracts.md) |
| Governance Layer | policy, approval, trace, audit, health, contract gate | [runtime_contracts.md](./runtime_contracts.md) |
| Delivery Layer | service APIs, Runtime Surface, Governance Timeline, SDK/facade | [extension_points.md](./extension_points.md) |
| Domain Agent Layer | manifest-driven agent assets and trial readiness | [domain_agent_development_guide.md](../guides/domain_agent_development_guide.md) |
| External Provider Layer | RAG/GraphRAG/document/voice data-plane services | [external_rag_provider_development.md](../guides/external_rag_provider_development.md) |

## What To Use Today

For normal chat:

```http
POST /api/chat
```

Use `execution_context.agent_id` and `execution_context.agent_role` when a business frontend needs to identify a domain agent. Do not add business-only fields into execution context without a formal contract.

For domain-agent discovery and trial readiness:

```http
GET /api/agents
POST /api/domain-agents/{agent_id}/grounded-answer-trial
POST /api/domain-agents/{agent_id}/grounded-answer-package-dry-run
POST /api/domain-agents/{agent_id}/grounded-answer-composition-trial
```

Repository-side smoke:

```powershell
python backend/scripts/domain_agent_trial_smoke.py --payload docs/examples/domain_agent_trial_payload.json --pretty
```

This only produces a `go / review / blocked` trial report. It does not call the provider, LLM, tools, MCP, `/api/chat`, memory, audit, trace, or source binding.

For runtime health and contract inspection:

```http
GET /api/health
GET /api/doctor
GET /api/runtime-profile
```

## Current Pause Lines

- Domain-agent grounded-answer control chain has reached repo-side trial readiness. Do not keep adding local evidence layers unless a real caller trial exposes a concrete gap.
- Default `/api/chat` retrieval injection remains disabled until provider readiness, representative eval evidence, and behavior promotion are approved through OpenSpec.
- New framework adapters must start with adapter boundary, lifecycle mapping, readiness, precheck, promotion gate, and non-goals. Do not route a new framework directly into main chat.
- External knowledge, document, and voice capabilities stay provider-first. Do not put vector databases, graph databases, OCR/layout/VLM engines, or ASR/TTS runtimes into the main backend by default.

## Recommended Reading Order

1. This entrypoint.
2. [current_architecture.md](./current_architecture.md)
3. [runtime_contracts.md](./runtime_contracts.md)
4. [extension_points.md](./extension_points.md)
5. [project_entrypoint_checklist.md](../guides/project_entrypoint_checklist.md)
6. [domain_agent_development_guide.md](../guides/domain_agent_development_guide.md)
7. [external_rag_provider_development.md](../guides/external_rag_provider_development.md)
8. [next_phase_hardening.md](../roadmap/next_phase_hardening.md)

## OpenSpec Workflow

Any change that affects runtime contracts, read models, governance semantics, provider boundaries, framework adapters, or default chat behavior must follow:

```text
specification -> implementation -> validation -> archive
```

Use `cmd /c openspec ...` on Windows for reliable CLI execution.
