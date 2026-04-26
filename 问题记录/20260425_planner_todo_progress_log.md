# 2026-04-25 Planner Todo Progress Log

## 2026-04-26 Update

- Phase 52：完成停止生成链路收口，修复前端中断请求不生效的问题
- 增加停止生成 smoke：`backend/scripts/chat_stop_generation_smoke.py`
- 增加统一测试手册：`docs/test_manual.md`
- 整理 `docs/README.md`、根 `README.md` 与 `问题记录/README.md`，收紧文档入口

## Context
The project needs to move closer to mature agent frameworks such as Claude Code. The main gap identified in the previous review was the absence of a first-class planner/todo layer.

## Objective
Deliver a minimal but reusable planner/todo capability that can support:

- goal capture
- plan generation
- step status management
- later multi-agent expansion

## Completed Today

### Backend

- Added planner domain models:
  - `PlanStatus`
  - `PlanRunRecord`
  - `PlanItemRecord`
- Added `PlannerService`
  - create/list/get plan
  - generate plan from objective
  - add/update/delete item
  - progress refresh and single active item enforcement
- Added planner router:
  - list plans
  - create plan
  - generate plan
  - update plan
  - add/update/delete item
- Registered planner router in server assembly

### Frontend

- Added `planner` store
- Added reusable `PlannerPanel.vue`
- Integrated planner panel into `ChatView.vue`
- Added inline chat entry for generating a plan from the current objective draft
- Wired `plan_updated` stream events into planner store refresh

### Chat Runtime Integration

- Added automatic planner state transition on chat execution:
  - request start -> current item becomes `in_progress`
  - assistant success -> current item becomes `completed`
- Added backend SSE payload for planner refresh
- Added minimal runtime handoff protocol:
  - specialized plan items now move through `ready -> handed_off -> executing -> merged`
  - chat service writes `agent_id` and handoff state before orchestrator execution
  - orchestrator receives `execution_context` and runs in role-focused pseudo-subagent mode
  - stream and non-stream chat paths are now aligned on planner state transitions

### Minimal Spawn / Merge Runtime

- Added `backend/services/subagent_service.py`
- Introduced normalized `SubagentContext`
- Added minimal spawned runtime protocol:
  - `subagent_spawned`
  - `subagent_collected`
  - `subagent_merged`
- Orchestrator now builds role-scoped system prompts through the dedicated subagent runtime layer
- This is the first step from pseudo handoff metadata to actual runtime sub-execution

### MCP Registry Foundation

- Added `backend/services/mcp_registry_service.py`
- Added `backend/routers/mcp.py`
- Added JSON-backed MCP registry persistence file
- Added capability catalog aggregation for enabled servers
- Registered MCP router group into reusable server assembly
- This gives the framework a stable external capability configuration boundary for later tool mounting

### MCP Runtime Capability Binding

- Added `backend/services/mcp_runtime_service.py`
- Enabled MCP capabilities are now converted into runtime tools before orchestration starts
- Orchestrator now syncs MCP capability tools into the shared tool registry on each run
- Capability tools resolve the primary enabled MCP provider at invocation time
- This is the first runtime bridge between MCP registry metadata and the harness tool system

### MCP Probe And Planner Capability Requirements

- Added `backend/services/mcp_adapter_service.py`
- MCP servers now support minimal probe / handshake status:
  - stdio -> local command discovery
  - http -> URL validation
- Added `POST /api/mcp/servers/{server_name}/probe`
- Planner items now support `required_capabilities`
- Chat execution context now carries required MCP capabilities into subagent mode
- This is the first bridge between planner task intent and MCP capability routing

### Runtime Capability Guard And Minimal Real MCP Dispatch

- Planner active items now enforce `required_capabilities` before execution starts
- If a required capability is missing or configured-but-unavailable:
  - the active plan item is marked `blocked`
  - planner emits a fresh `plan_updated`
  - chat returns a deterministic blocked response instead of continuing blindly
- Orchestrator now has a defensive capability guard for specialized execution context
- MCP adapter no longer only returns placeholder routing text:
  - `stdio` providers now receive a JSON payload via subprocess stdin/stdout
  - `http` providers now receive a JSON POST payload
- Added backend regression coverage for:
  - capability validation
  - stdio/http adapter dispatch
  - planner blocked transition
  - chat lifecycle capability blocking

### MCP Session Handshake Skeleton

- Added `backend/services/mcp_session_service.py`
- MCP now has a first session-level handshake path:
  - sends `initialize`
  - sends `tools/list`
  - normalizes `protocol_version / server_info / capabilities / tools`
  - returns a minimal audit array for each handshake phase
- Added `POST /api/mcp/servers/{server_name}/handshake`
- Adapter now exposes a generic JSON-RPC session request path on top of stdio/http transport dispatch
- This is not a full MCP session runtime yet, but it is the first concrete step from transport-level dispatch toward protocol-level compatibility

### MCP Tools Call And Session Cache

- `McpSessionService` now caches handshake results per server
- Added protocol-level `tools/call`
- Session layer can now:
  - resolve `capability -> tool_name`
  - use `server.metadata.capability_tools` as the primary mapping source
  - fall back to handshake tool inference when possible
- `McpRuntimeService` now prefers session-level capability execution and only falls back to the transport adapter if session execution fails
- Added management API:
  - `POST /api/mcp/servers/{server_name}/tools/{tool_name}/call`
- Added regression coverage for:
  - handshake cache reuse
  - normalized `tools/call` result
  - capability execution through mapped MCP tool
  - runtime fallback from session call to adapter call

### Frontend MCP Management Panel

- Added `frontend-vue/src/stores/mcp.js`
- Added `frontend-vue/src/components/McpManagementPanel.vue`
- Integrated MCP management into `frontend-vue/src/views/SettingsView.vue`
- The frontend can now:
  - list MCP servers
  - create / update / delete server records
  - enable / disable servers
  - inspect capability catalog
  - trigger probe / handshake
  - run `tools/call` manually for debugging
- Added frontend regression coverage for the MCP panel's render and create flow
- Frontend validation passed:
  - `npm test` -> 7 test files / 24 tests passed
  - `npm run build` -> passed

### Assignment Semantics

- Added per-item multi-agent preparation fields:
  - `agent_role`
  - `agent_id`
  - `handoff_status`
- Added heuristic role suggestion during plan generation
- Added planner UI controls for role and handoff state editing

### Documentation

- Added `docs/planner_todo_framework_plan.md`
- Planned docs index update

## Architectural Value

- The project now has a visible "goal -> plan -> execution state" layer.
- This creates the correct base for later:
  - subagent assignment
  - planner event streaming
  - task approval checkpoints
  - MCP capability binding

## Current Limitations

- The current handoff is not a true spawned subagent runtime yet.
- The current subagent runtime is isolated but not parallelized; no scheduler/fan-out yet.
- Planner state still enters runtime through chat integration instead of a shared scheduler/event bus.
- Planner has no dedicated frontend automated tests in this phase.
- MCP registry, probe, runtime binding, minimal transport dispatch, handshake skeleton, `tools/call`, and frontend management panel now exist, but the full MCP protocol/session model is still missing.

## Next Suggested Work

1. Add parallel child scheduler and true multi-subagent fan-out / fan-in.
2. Add planner automated tests for frontend store/component.
3. Introduce `/plan` and `/todo` command support.
4. Add planner history / audit trail.
5. Add long-lived MCP session lifecycle, health/retry governance, stronger capability-tool governance, and generalized scheduler-grade capability policy.

## Enterprise Roadmap Alignment

- Added [docs/agent_framework_enterprise_roadmap.md](../docs/agent_framework_enterprise_roadmap.md) as the new top-level implementation roadmap.
- Consolidated the current major remaining gaps into one staged plan:
  - true multi-agent scheduler
  - MCP long-lived runtime
  - scheduler governance and audit
  - skill runtime integration
  - learning governance
  - operator-facing productization
- Confirmed the immediate next implementation priority remains the same:
  - build the true multi-agent scheduler first
  - use it as the runtime foundation for later MCP, skill, and learning upgrades
- This roadmap is intended to replace ad hoc prioritization across separate topic plans and give the project a single enterprise-oriented execution sequence.

## Phase A First Delivery

- Added `backend/services/scheduler_service.py` as the first real scheduler layer.
- Active plan items can now fan out into multiple child executions when the item declares more than one target role.
- Child execution records are now persisted in `plan item metadata` and include:
  - `child_execution_id`
  - `agent_role`
  - `agent_id`
  - `status`
  - `summary`
  - `error`
- Added minimal `fan-out -> collect -> merge` runtime support:
  - stream and non-stream chat paths can now execute multiple child contexts sequentially
  - child results are merged back into one final assistant response
  - partial failure is now represented explicitly through `merge_status`
- Planner serialization now exposes:
  - `child_executions`
  - `merge_summary`
- Added regression coverage for:
  - scheduler fan-out context creation
  - partial failure merge behavior
  - planner serialization of child execution state
  - chat path scheduler execution-context construction
- Added Planner frontend visibility for scheduler state:
  - `child_executions`
  - `merge_summary`
  - merged output
  - child-level summary / error rendering
- Added frontend regression coverage for planner scheduler display:
  - `frontend-vue/src/components/__tests__/PlannerPanel.test.js`
- Related implementation record:
  - [20260425_framework_phase36_implementation.md](./20260425_framework_phase36_implementation.md)

## Phase A Parallel Fan-Out Upgrade

- Upgraded scheduled child execution from sequential fan-out to first-pass parallel fan-out.
- `backend/services/chat_service.py` now:
  - creates one child task per child execution context
  - runs child tasks concurrently
  - collects finished child runs via `asyncio.as_completed()`
  - updates planner/scheduler state from the main coordination loop
- Each child execution now uses its own orchestrator instance instead of reusing a single shared orchestrator object.
- Added regression coverage for scheduled parallel fan-out stream behavior.
- Related implementation record:
  - [20260425_framework_phase37_implementation.md](./20260425_framework_phase37_implementation.md)

## Phase A Scheduler Governance Upgrade

- Added first-pass scheduler execution policy:
  - `timeout_seconds`
  - `max_retries`
  - `cancel_on_failure`
- Child execution records now retain richer governance metadata:
  - retry count
  - retry error
  - error kind
  - started/completed/cancelled timestamps
- Fan-out runtime now supports:
  - timeout-bounded child execution
  - bounded retries
  - cancellation of remaining child tasks after a configured failure
- Added runtime scheduler events for governance transitions:
  - `scheduler_retry`
  - `subagent_cancelled`
  - `scheduler_cancelled`
- Added regression coverage for timeout -> retry -> failure and cancellation flow.
- Related implementation record:
  - [20260425_framework_phase38_implementation.md](./20260425_framework_phase38_implementation.md)

## Phase A Audit Trail And Timeline

- Added scheduler audit trail persistence to planner item metadata.
- Planner item serialization now exposes:
  - `audit_trail`
- Planner frontend now renders a timeline block for scheduler/runtime events.
- Audit trail currently covers:
  - fan-out preparation
  - execution start
  - child running/completed/failed/retrying/cancelled
  - scheduler cancelled
  - scheduler merged
- Added regression coverage for:
  - audit trail append/read behavior
  - planner serialization of audit trail
  - planner timeline rendering
- Related implementation record:
  - [20260425_framework_phase39_implementation.md](./20260425_framework_phase39_implementation.md)

## Phase A Unified Run Trace Upgrade

- Added unified `run_trace` support in `backend/services/scheduler_service.py`.
- Normalized trace entries now include:
  - `timestamp`
  - `source`
  - `event_type`
  - `severity`
  - `summary`
  - `detail`
  - `payload`
- `run_trace` currently covers:
  - scheduler fan-out / execution / merge events
  - child running / completed / failed / retrying / cancelled events
  - capability blocked events
  - scheduler cancellation events
- Planner serialization now exposes:
  - `run_trace`
- Planner frontend now renders a dedicated run-trace block.
- Added regression coverage for:
  - scheduler unified trace recording
  - planner serialization of `run_trace`
  - planner panel `run_trace` rendering
- Related implementation record:
  - [20260425_framework_phase40_implementation.md](./20260425_framework_phase40_implementation.md)

## Phase A Runtime Tool And Permission Trace Upgrade

- Added runtime-event-to-trace mapping in `backend/services/chat_service.py`.
- Unified planner-item `run_trace` now also records:
  - `tool_permission_required`
  - `tool_denied`
  - `tool_called`
  - `tool_failed`
  - `mcp_tool_called`
  - `mcp_tool_failed`
- Covered runtime paths now include:
  - standard stream chat
  - standard non-stream chat
  - scheduler parallel child execution
- MCP runtime tool calls are now normalized as `source=mcp` events when tool names begin with `mcp_`.
- Permission waiting / denial now appears in the same run trace model as scheduler and capability events.
- Added regression coverage for:
  - stream trace recording of permission + MCP tool events
  - non-stream trace recording of tool failure events
- Related implementation record:
  - [20260425_framework_phase41_implementation.md](./20260425_framework_phase41_implementation.md)

## Phase A Permission Approval Trace Upgrade

- Added `backend/services/run_trace_service.py` for router/service-level unified trace appends.
- `RunTraceService` can now append trace records to the latest active planner item for one conversation.
- Permission approval APIs now append run-trace events:
  - `permission_approved`
  - `permission_denied`
- `backend/harness/permission_service.py` now restores persisted requests before approve/deny when the in-memory copy is missing.
- Added regression coverage for:
  - router-level permission approval trace append
  - router-level permission denial trace append
  - run-trace service append behavior
- Related implementation record:
  - [20260425_framework_phase42_implementation.md](./20260425_framework_phase42_implementation.md)

## Phase D Skill Runtime Integration First Pass

- Added `backend/services/skill_runtime_service.py`.
- Runtime now loads enabled skills from storage, parses `SKILL.md`, and scores deterministic matches by:
  - user-message overlap
  - `agent_role`
  - `required_capabilities`
  - direct trigger / skill-name hits
- `backend/orchestrator.py` now:
  - injects selected skill context as runtime system prompt
  - emits `status_kind=runtime_skills`
  - persists `runtime_skill` and `runtime_skill_effect` artifacts
- Unified planner-item `run_trace` now records:
  - `source=skill`
  - `event_type=runtime_skills_selected`
- Added regression coverage for:
  - runtime skill matching
  - runtime skill artifact persistence
  - runtime skill status to run-trace mapping
- Related implementation record:
  - [20260425_framework_phase43_implementation.md](./20260425_framework_phase43_implementation.md)

## Phase D Skill Runtime Governance First Pass

- Runtime skill frontmatter now supports lightweight governance fields:
  - `priority`
  - `activation` / `activation_mode`
  - `domain`
- Runtime now enforces activation policy:
  - `manual` skills do not auto-select
  - `role_only` skills require matching `agent_role`
- Added deterministic conflict suppression for overlapping runtime skill candidates:
  - compare runtime score first
  - then compare priority
  - then use stable ordering
- Suppressed candidates now remain visible in `skipped_skills` / `skipped_items` as `conflict_suppressed`.
- Added regression coverage for:
  - manual activation suppression
  - role-only activation matching
  - domain conflict resolution by priority
- Related implementation record:
  - [20260425_framework_phase44_implementation.md](./20260425_framework_phase44_implementation.md)

## Phase Stability Startup Diagnostics And Smoke

- Added `backend/services/startup_diagnostics_service.py` for unified startup readiness checks.
- Added `GET /api/health` through `backend/routers/health.py`.
- Added CLI helpers:
  - `backend/scripts/doctor.py`
  - `backend/scripts/smoke_check.py`
- Current diagnostics cover:
  - `.env` and default model configuration
  - database connectivity
  - critical filesystem paths
  - SPA build artifact readiness
  - available server presets
- Added regression coverage for:
  - diagnostics report aggregation
  - `/api/health` route response
- Related implementation record:
  - [20260425_framework_phase45_implementation.md](./20260425_framework_phase45_implementation.md)

## Phase Stability Auth And Conversation Smoke

- Added `backend/scripts/auth_session_smoke.py`.
- Current smoke flow now validates:
  - guest login
  - current-user lookup
  - conversation creation
  - conversation list
  - conversation detail
- Added automated regression coverage using temporary SQLite:
  - `tests/agent_framework/test_auth_conversation_smoke.py`
- Related implementation record:
  - [20260425_framework_phase46_implementation.md](./20260425_framework_phase46_implementation.md)

## Phase Stability Chat SSE Smoke

- Chat stream route now emits fallback `done` when runtime content exists but upstream omitted a final done event.
- Added `backend/scripts/chat_stream_smoke.py`.
- Added automated regression coverage:
  - `tests/agent_framework/test_chat_stream_smoke.py`
- Current chat stream smoke validates:
  - `conversation_id`
  - streamed `content`
  - final `done`
  - fallback done aggregation
- Related implementation record:
  - [20260426_framework_phase47_implementation.md](./20260426_framework_phase47_implementation.md)

## Phase Stability Chat Empty Response Handling

- Chat route now returns a fallback content + done pair when the upstream stream completes with no assistant content.
- Frontend conversation store now finalizes messages immediately on SSE `error` events.
- Added `backend/scripts/chat_empty_response_smoke.py`.
- Added automated regression coverage:
  - `tests/agent_framework/test_chat_empty_response_smoke.py`
  - updated `frontend-vue/src/stores/__tests__/conversation.test.js`
- Related implementation record:
  - [20260426_framework_phase48_implementation.md](./20260426_framework_phase48_implementation.md)

## Phase Stability Frontend Regression Closure And Error Smoke

- Fixed frontend conversation finalize flow so returned assistant objects stay in sync with rendered messages.
- Re-ran frontend validation successfully:
  - `npm test`
  - `npm run build`
- Added `backend/scripts/chat_error_event_smoke.py`.
- Related implementation record:
  - [20260426_framework_phase49_implementation.md](./20260426_framework_phase49_implementation.md)

## Phase Storage Default SQLite For Demo

- Demo backend now defaults to `DB_MODE=sqlite`.
- Local state is stored under `.myagent/app.db` by default.
- MySQL database creation bootstrap now only runs when `DB_MODE=mysql`.
- Startup diagnostics now surface storage mode and actual connection target.
- Related implementation record:
  - [20260426_framework_phase50_implementation.md](./20260426_framework_phase50_implementation.md)

## Phase Demo Runbook Closure

- Added `docs/demo_runbook.md`.
- Centralized:
  - startup steps
  - smoke-check order
  - demo flow
  - troubleshooting
  - SQLite/MySQL mode guidance
- Updated `README.md` and `docs/README.md` to point to the runbook.
- Related implementation record:
  - [20260426_framework_phase51_implementation.md](./20260426_framework_phase51_implementation.md)
