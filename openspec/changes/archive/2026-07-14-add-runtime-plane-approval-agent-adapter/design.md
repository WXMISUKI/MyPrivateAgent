## Context

The runtime plane now has two Stage 1 vertical slices:

- `simple_agent`: validates request/event/result envelope and adapter boundary.
- `tool_agent`: validates a controlled read-only tool call and normalized tool result.

The remaining MVP gap is approval interruption. Production systems cannot allow high-risk tool calls to run merely because a model emitted a tool call. The next most valuable slice is therefore a minimal adapter that converts high-risk tool intent into a normalized approval-pending envelope without executing the tool or creating a production approval record.

## Goals / Non-Goals

**Goals:**

- Add a focused `ApprovalAgentAdapter` that reuses existing `ExecutionRequest`, `ExecutionEvent`, `ExecutionResult`, `Agent`, and `ToolDef` contracts.
- Stop before executing high-risk or approval-required tools.
- Emit a compact, deterministic approval interrupt envelope that governance code can later consume.
- Keep tests small and deterministic.

**Non-Goals:**

- Do not call `ApprovalEngineService`.
- Do not persist approval requests.
- Do not implement resume or approved continuation.
- Do not change default `/api/chat`.
- Do not introduce LangGraph, AgentRun, ADK, or OpenAI Agents SDK runtime dependencies in this slice.
- Do not create a general workflow engine, checkpoint engine, sandbox, or scheduler.

## Decisions

### 1. Use adapter-level interception instead of changing graph engine semantics

The adapter will invoke the existing Agent graph only through the first model response and then inspect emitted tool calls. If a tool call targets a high-risk or approval-required tool, the adapter emits `approval_required` and returns `approval_pending`.

Rationale: this proves the normalized approval boundary without expanding the graph engine or `ToolNode` into a policy runtime.

Alternative considered: add approval awareness directly to `ToolNode`. Rejected for this slice because it would mix runtime-plane MVP proof with execution engine behavior.

### 2. Use compact metadata, not raw framework payload

The approval event metadata will include request id, agent id, tool name, risk level, permission level, approval reason, and sanitized args summary. It will not include callables, clients, raw provider objects, or large payloads.

Rationale: governance surfaces need stable summaries, not framework-native internals.

### 3. Keep approval pending as terminal for this slice

The adapter result status will be `approval_pending`, and no continuation API will be added.

Rationale: the current goal is to prove a safe stop line. Resume belongs to a later explicit change that can connect the approval lifecycle and replay semantics.

## Risks / Trade-offs

- [Risk] The adapter only inspects deterministic model-call output and does not represent all future framework interrupts. -> Mitigation: treat this as Stage 1 local adapter proof, not production framework integration.
- [Risk] Approval metadata could grow too large. -> Mitigation: include compact summaries only and add tests for key fields rather than raw payload equality.
- [Risk] Future resume behavior may need a richer descriptor. -> Mitigation: keep `approval_request` metadata explicit enough to become a later continuation descriptor source.
