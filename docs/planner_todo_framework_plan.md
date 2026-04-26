# Planner Todo Framework Plan

## Goal
Build a Claude Code style minimal planner/todo layer on top of the current reusable agent demo so the project is not only "chat + tools", but also "goal -> plan -> execution state".

## Scope For This Phase

1. Add backend planner domain models.
2. Add planner service and REST API.
3. Add frontend planner store and reusable panel component.
4. Integrate planner panel into chat view.
5. Add implementation log and keep the docs index current.

## Delivered In This Phase

- `backend/models.py`
  - Added `PlanStatus`
  - Added `PlanRunRecord`
  - Added `PlanItemRecord`
- `backend/services/planner_service.py`
  - Plan CRUD
  - Item CRUD
  - Single active `in_progress` item enforcement
  - Progress summary refresh
  - Minimal automatic plan generation from objective text
- `backend/routers/plans.py`
  - `GET /api/plans`
  - `POST /api/plans`
  - `POST /api/plans/generate`
  - `GET /api/plans/{plan_id}`
  - `PATCH /api/plans/{plan_id}`
  - item add/update/delete endpoints
- `frontend-vue/src/stores/planner.js`
  - load/create/generate/update/add/delete plan actions
- `frontend-vue/src/components/PlannerPanel.vue`
  - planner/todo panel UI
- `frontend-vue/src/views/ChatView.vue`
  - planner panel integration
  - chat input based objective draft
  - inline "generate plan" entry
- chat execution integration
  - request start marks current plan item as `in_progress`
  - successful assistant completion marks current item as `completed`
  - backend emits `plan_updated` SSE event
  - frontend conversation stream refreshes planner store from runtime event
- planner assignment semantics
  - plan items now support `agent_role`
  - plan items now support `agent_id`
  - plan items now support `handoff_status`
  - generated plan items receive heuristic initial role suggestions
- minimal runtime handoff loop
  - chat start emits `plan_updated` for `in_progress`
  - specialized plan items move through `ready -> handed_off -> executing -> merged`
  - orchestrator now receives `execution_context`
  - orchestrator emits runtime `status` for pseudo-subagent mode
  - non-stream and stream chat paths now keep planner transitions consistent
- minimal spawned subagent runtime
  - added `SubagentRuntimeService`
  - specialized plan items now create an isolated subagent execution context
  - orchestrator emits `subagent_spawned -> subagent_collected -> subagent_merged`
  - role-focused system prompts are now built from a dedicated subagent runtime layer
- planner capability enforcement
  - active plan items now enforce `required_capabilities` before execution begins
  - missing/unavailable capabilities block the plan item instead of silently continuing
  - chat route returns a deterministic blocked response and planner status update
- MCP execution bridge
  - MCP capability tools no longer stop at placeholder text
  - stdio providers now receive a JSON payload over subprocess stdin/stdout
  - http providers now receive a JSON POST request through the runtime adapter

## Why This Matters

- It creates a first-class execution state layer for later multi-agent orchestration.
- It gives the demo a visible and reusable planning capability instead of only conversational UX.
- It establishes stable API and UI boundaries for future work:
  - planner events
  - subagent assignment
  - approval checkpoints
  - MCP-backed task execution

## Known Gaps

- The current handoff is still a pseudo-subagent protocol, not a real spawned worker runtime.
- `agent_id` is now stable runtime metadata, but still not backed by an independent execution container/thread.
- Planner events are emitted from chat integration, not from a generalized orchestrator/harness event bus.
- No planner-specific frontend tests yet.
- No dedicated planner page or timeline; current entry is embedded in chat view.
- No parallel child scheduler yet; current subagent runtime is isolated but still single-process and single-child.
- MCP registry and minimal runtime dispatch now exist, but there is still no full MCP session/connector layer.

## Recommended Next Steps

1. Add parallel child scheduler and true multi-subagent fan-out/fan-in.
2. Emit planner runtime events from a shared orchestrator/harness event layer instead of chat route only.
3. Add planner store/component tests and one end-to-end planner smoke test.
4. Add planner commands such as `/plan`, `/todo`, `/focus`.
5. Add a planner timeline or audit log.
6. Add scheduler-grade capability policy, fallback strategy, and MCP execution audit trail.
