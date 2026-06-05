# Internal Agent Control Tasks

> Scope: MyPrivateAgent-side control-plane work that does not require the external RAG / GraphRAG provider project to be production-ready.

## Current Decision

The external RAG / GraphRAG provider remains an active but external data-plane dependency. While that project is still under development, MyPrivateAgent should keep moving on internal control contracts that are useful on their own and are required before default retrieval injection becomes safe.

`add-agent-grounding-policy-contract` and `add-promptops-versioned-prompt-contract` have been implemented and archived. The current Phase 22 implementation line is `add-agent-memoryops-lifecycle-contract`.

## Sequenced Task Queue

| Order | OpenSpec change | Goal | External provider dependency | Implementation stance |
|---|---|---|---|---|
| 1 | `add-agent-grounding-policy-contract` | Normalize agent grounding policy, citation requirement, ungrounded fallback, and source ACL semantics | No for visibility; yes later for enforcement | Done |
| 2 | `add-promptops-versioned-prompt-contract` | Turn `/prompts` CRUD into versioned prompt governance with variables, eval binding, approval, rollout, and rollback | No | Done |
| 3 | `add-agent-memoryops-lifecycle-contract` | Define hot session state, conversation summary, long-term memory, TTL, deletion, confidence, conflict, and injection trace | No | Phase 22 current |
| 4 | `add-multiturn-agent-evaluation-gate` | Add scenario-based regression for prompt, grounding, memory, tool, and refusal behavior | Partial | Spec before changing default retrieval injection |
| 5 | Later focused changes | Multimodal taxonomy, workflow/chatflow, enterprise connectors, provider ops | Depends on scenario | Defer until P0/P1 contracts stabilize |

## Grounding Policy Slice

Why first:

- It is the behavior-control layer required before `/api/chat` can safely use retrieved knowledge by default.
- It does not need a finished external provider to expose policy/readiness.
- It gives PromptOps, MemoryOps, and multi-turn eval a stable grounding vocabulary to refer to.

First implementation boundaries:

- Read `grounding_policy` from `backend/domain_agents/<agent_id>/agent.yaml`.
- Support existing `retrieval` fields as compatibility input.
- Expose normalized policy through Runtime Surface.
- Report readiness as visibility-only.
- Do not change default `/api/chat` behavior.

Done means:

- The OpenSpec change is implemented and archived.
- `domain_agent_registry` exposes normalized grounding policy.
- Existing `rag_source_registry` and `knowledge_graph_registry` remain stable.
- Focused backend tests and strict OpenSpec validation pass.

## Next After Grounding

PromptOps should follow grounding policy because prompt versions and activation need to know which grounding policy and eval set they are being tested against.

MemoryOps should follow PromptOps or run as a separate contract-only change if we need durable long-term memory semantics earlier.

Multi-turn eval should be created before any behavior-affecting promotion such as default knowledge injection, automatic grounding enforcement, or prompt rollout.

## Phase 21 PromptOps Slice

Current implementation boundary:

- Expose existing `SystemPrompt` records as a read-only PromptOps contract.
- Keep legacy `/api/learnings/prompts` CRUD and runtime prompt injection unchanged.
- Infer `version = "1"` for legacy prompts unless a `version:<value>` tag exists.
- Report `status = active` for active prompts and `status = archived` for inactive prompts unless an explicit `status:draft` or `status:review` tag exists.
- Extract `{{variable}}` template placeholders into a minimal variables schema.
- Preserve optional governance tags such as `owner:<id>`, `grounding_policy:<id>`, `eval_set:<id>`, `approval:<state>`, `rollout:<mode>`, and `rollback_target:<version>`.

Done means:

- `add-promptops-versioned-prompt-contract` is implemented and archived.
- A focused PromptOps read model is available without database migration.
- Focused tests and strict OpenSpec validation pass.
- Chat behavior and default retrieval injection remain unchanged.

## Phase 22 MemoryOps Slice

Current implementation boundary:

- Expose existing `AgentMemoryService` runtime instruction layers as `runtime_instruction_memory` entries.
- Expose latest durable compact summaries as `conversation_summary` entries when a `conversation_id` is provided.
- Report posture for `hot_session_state`, `long_term_memory`, and `retrieved_knowledge_evidence` without introducing new storage.
- Keep retrieved knowledge as evidence by default; promotion to durable memory must remain explicit in a later change.
- Keep `/api/chat`, context packing, prompt injection, and retrieval behavior unchanged.

Done means:

- `add-agent-memoryops-lifecycle-contract` is implemented and archived.
- `GET /api/admin/memoryops/contract` returns a stable visibility-only registry.
- Focused MemoryOps tests and strict OpenSpec validation pass.
- Multi-turn eval can reference grounding, prompt, and memory lifecycle vocabulary in the next phase.
