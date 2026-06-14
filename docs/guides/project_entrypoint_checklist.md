# Project Entrypoint Checklist

> Use this checklist to choose the right path before adding more implementation.

## 1. Local Verification

- [ ] Read [agent_runtime_control_plane_entrypoint.md](../architecture/agent_runtime_control_plane_entrypoint.md).
- [ ] Confirm active OpenSpec changes:

```powershell
cmd /c openspec list --json
```

- [ ] Validate specs after doc/spec work:

```powershell
cmd /c openspec validate --all --strict
```

- [ ] For runtime contract changes, prefer focused backend tests or `backend/scripts/runtime_contract_smoke.py` over broad build commands.

## 2. Domain Agent Trial

- [ ] Create or inspect `backend/domain_agents/<agent_id>/agent.yaml`.
- [ ] Confirm the agent is visible:

```http
GET /api/agents
```

- [ ] Inspect `capability_linkage` for missing Tool / Skill / MCP declarations.
- [ ] Run repo-side smoke when the caller has evidence:

```powershell
python backend/scripts/domain_agent_trial_smoke.py --payload docs/examples/domain_agent_trial_payload.json --pretty
```

- [ ] Treat `go` as permission to start caller repo-side trial only.
- [ ] Treat `review` as a human review state, not production readiness.
- [ ] Treat `blocked` as a hard stop until blockers are resolved.
- [ ] Do not enable default `/api/chat` retrieval injection from trial-pack success alone.

## 3. External Provider Boundary

- [ ] Keep RAG/GraphRAG provider logic outside MyPrivateAgent.
- [ ] Start from the provider onboarding catalog:

```http
GET /api/provider-onboarding
GET /api/provider-onboarding/{onboarding_id}/readiness
```

- [ ] Inspect current live management status:

```http
GET /api/service-providers
```

- [ ] Generate acceptance evidence before caller-side use:

```powershell
python backend/scripts/provider_onboarding_acceptance_smoke.py --onboarding-id knowledge-rag-provider --pretty
```

- [ ] Treat `accepted` as explicit managed-provider consumption only.
- [ ] Use provider capability contracts such as `knowledge.rag.retrieve` and `knowledge.graph.query`.
- [ ] Keep OCR/Layout/VLM, ASR/TTS, vector databases, graph databases, embeddings, and rerankers out of the main backend unless a later OpenSpec explicitly promotes them.
- [ ] Document provider health, catalog, request/response shape, and failure modes before caller-side promotion.
- [ ] Do not infer default `/api/chat` RAG, GraphRAG, source binding, or final answer policy promotion from provider acceptance.

## 4. Runtime / SDK Extension

- [ ] Identify the layer first: Runtime Core, Capability, Governance, Delivery, or Domain Agent.
- [ ] Read [runtime_contracts.md](../architecture/runtime_contracts.md) before changing contract fields.
- [ ] For Embedded SDK / Harness work, check the current preview boundary in `backend/agent_framework/sdk.py`, `backend/agent_framework/harness.py`, and the embedded SDK OpenSpec specs before adding new behavior.
- [ ] Generate Embedded SDK recovery acceptance evidence before treating registry-backed recovery as explicitly consumable:

```powershell
python backend/scripts/embedded_sdk_recovery_acceptance_smoke.py --scenario accepted --pretty
```

- [ ] Treat Embedded SDK recovery `accepted` as explicit SDK consumption readiness only.
- [ ] If a change affects Embedded SDK, ToolRuntime, Approval, Recovery, Worker Ownership, Query Control, or Runtime Surface, create an OpenSpec change first.
- [ ] Keep new evidence compact and machine-readable.
- [ ] Do not copy Python callable, provider client, active stream iterator, or full tool result bodies into governance payloads.
- [ ] Do not infer worker lease, background auto-recovery, distributed execution, real LLM execution, or default `/api/chat` behavior from Embedded SDK recovery acceptance.

## 5. Framework Adapter Extension

- [ ] Treat the framework as an execution adapter candidate.
- [ ] Define lifecycle mapping, input translation, event translation, output translation, readiness, precheck, failure classification, and promotion gate.
- [ ] Keep framework-native raw payloads out of primary frontend/governance contracts.
- [ ] Do not route new framework adapters into default main chat without an explicit promotion change.

## 6. Stop Conditions

Pause and re-plan when:

- [ ] A direction adds only another evidence layer without moving caller usability or runtime maturity forward.
- [ ] A proposed change would alter `/api/chat` behavior without provider readiness and eval evidence.
- [ ] A provider/data-plane feature starts moving heavy runtime dependencies into the main backend.
- [ ] A frontend governance enhancement requires inventing backend contract semantics in the UI.
- [ ] A new integration bypasses OpenSpec, ToolRuntime, Policy/Approval, Runtime Trace, or adapter boundaries.

## 7. Default Next Direction

When no active change exists and no real caller trial is blocked, default back to runtime/control-plane priorities:

1. Embedded SDK durability and recovery maturity.
2. Execution Loop integration with ToolRuntime, reviewer, fallback, and model degradation policy.
3. Framework adapter authoring checklist / promotion review before adding another adapter.
4. Runtime Surface contract assembler cleanup.
5. Governance Timeline slimming only when it reduces maintenance cost.
