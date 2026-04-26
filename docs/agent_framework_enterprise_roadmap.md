# Agent Framework Enterprise Roadmap

## Goal

Build the current reusable agent demo into a more mature general-purpose agent framework that moves closer to Claude Code style execution quality, governance, and extensibility.

This roadmap focuses on the most important missing capabilities identified in the current project review:

1. true multi-agent scheduling
2. long-lived MCP runtime
3. skill runtime integration
4. learning governance
5. observability and audit
6. enterprise-grade scheduling governance

## Current Baseline

The project already has a strong phase-one foundation:

- reusable chat + harness + orchestrator skeleton
- planner/todo domain and panel
- pseudo-subagent handoff and minimal spawned runtime protocol
- MCP registry, probe, handshake skeleton, `tools/call`, runtime capability binding, and settings panel
- runtime learning injection and feedback-to-learning minimum loop
- focused frontend regression coverage and backend service tests

This means the project is no longer a simple chat demo. It is now a reusable framework demo with a clear execution architecture. The next work should prioritize maturity and runtime determinism rather than more UI surface area.

## Priority Principles

### P0 Principles

- prioritize execution correctness over new surface features
- prioritize scheduler/runtime boundaries over ad hoc chat-route logic
- prioritize governance and auditability over implicit magic
- each phase must leave behind testable boundaries and clear rollback points

### Prioritization Order

1. true multi-agent scheduler
2. MCP long-lived runtime
3. scheduler governance and audit
4. skill runtime integration
5. learning governance
6. broader UX and operator tooling

## Phase Plan

## Phase A: True Multi-Agent Scheduler

### Objective

Upgrade the current pseudo handoff model into a real scheduler that can fan out plan items into child executions and merge results back into the parent run.

### Scope

- introduce a scheduler service independent from chat route control flow
- support one parent run spawning multiple child executions
- add child execution states such as `queued`, `running`, `completed`, `failed`, `cancelled`
- support `fan-out -> collect -> merge` for plan items
- persist child execution metadata and merge summaries
- emit scheduler events through a shared runtime event layer

### Expected Deliverables

- `SchedulerService` or equivalent runtime coordinator
- planner item to child execution mapping
- merge strategy abstraction for child result aggregation
- scheduler-focused event schema and backend tests
- minimal frontend planner audit/history visibility

### Acceptance Criteria

- one planner item can produce multiple child executions
- parent plan item can remain open until all required children return
- failures are captured deterministically and do not silently disappear
- merged result is stored and visible through API
- at least one regression test covers successful fan-out/fan-in
- at least one regression test covers partial failure handling

### Risks

- state explosion if parent/child transitions are not normalized
- duplicate execution if retries are not idempotent
- merge quality issues if child responsibility boundaries are vague

## Phase B: MCP Long-Lived Runtime

### Objective

Promote the current MCP registry and minimal session skeleton into a stable long-lived runtime with reusable sessions, health status, and retry governance.

### Scope

- add session lifecycle management
- add health cache and probe freshness policy
- add reconnect / invalidation rules
- add per-server session state tracking
- add capability-provider selection policy
- add MCP audit trail for handshake, `tools/list`, `tools/call`, errors, and retries

### Expected Deliverables

- `McpSessionManager` or equivalent long-lived runtime layer
- reusable connection/session cache
- session invalidation and reconnect policy
- health and freshness metadata in MCP API
- backend tests for reconnect, invalid session reuse, and degraded provider fallback

### Acceptance Criteria

- repeated calls to the same MCP server reuse a valid session when possible
- unhealthy sessions are invalidated and re-established deterministically
- runtime can distinguish configuration errors, probe failures, and call failures
- MCP call history is queryable for debugging and audit

### Risks

- leaking stale sessions or subprocesses
- masking infrastructure issues behind silent fallback
- health state drift if no freshness window is enforced

## Phase C: Scheduler Governance And Audit

### Objective

Add enterprise-grade runtime governance so execution is policy-driven instead of best-effort.

### Scope

- capability policy engine at scheduler level
- blocking, fallback, retry, and approval checkpoints
- planner audit trail and scheduler timeline
- unified run trace for planner, subagent, tool, and MCP events
- deterministic error classification

### Expected Deliverables

- policy evaluator for plan execution
- planner timeline / audit API
- unified trace model for run, handoff, tool, and MCP records
- operator-readable blocked / fallback / retry reasons

### Acceptance Criteria

- blocked items show explicit cause and recovery guidance
- fallback behavior is configured rather than hidden in code paths
- retries are bounded and recorded
- planner run can be reconstructed from audit logs

### Risks

- inconsistent policy behavior if rules are duplicated across services
- reduced usability if blocking reasons are not surfaced clearly

## Phase D: Skill Runtime Integration

### Objective

Move skills from CRUD assets into first-class runtime participants.

### Scope

- skill discovery during orchestration
- skill matching against planner item, user intent, and required capabilities
- controlled prompt/tool/context injection from skills
- skill activation policy and priority resolution
- skill audit and hit attribution

### Expected Deliverables

- `SkillRuntimeService` or equivalent runtime selector
- skill activation records per run
- skill-to-tool / skill-to-prompt binding strategy
- tests for matching, priority conflict, and disabled skill fallback

### Acceptance Criteria

- runtime can explain why a skill was selected
- skill selection is deterministic under conflicting candidates
- disabled or invalid skills do not break the main run

### Risks

- uncontrolled prompt inflation
- overlapping skills creating unpredictable behavior
- poor attribution if skill hits are not recorded

## Phase E: Learning Governance

### Objective

Upgrade the current feedback and learning loop into a governed learning system that can be evaluated, versioned, rolled back, and isolated by domain.

### Scope

- learning quality score
- conflict detection and resolution workflow
- versioning and approval state
- rollback / disable controls
- domain / tenant / project isolation
- learning hit attribution and effect evaluation

### Expected Deliverables

- governed learning model extensions
- review workflow for promoted runtime knowledge
- hit/effect attribution records
- learning analytics and conflict APIs

### Acceptance Criteria

- one learning can be disabled or rolled back without deleting history
- conflicting learnings are surfaced explicitly
- runtime can attribute a response to the learning entries it consumed
- learning quality can be ranked and reviewed

### Risks

- noisy feedback contaminating runtime prompts
- conflicting learnings silently degrading output quality
- no clear owner for learning approval decisions

## Phase F: Operator UX And Productization

### Objective

Finish the framework as a reusable operator-facing demo, not just an engineering skeleton.

### Scope

- planner timeline UI
- scheduler state panel
- MCP health dashboard and call history
- learning review console
- richer command palette integration for planning and operations

### Acceptance Criteria

- operators can understand why the agent acted, blocked, retried, or failed
- core governance states are visible without reading raw logs
- demo can be shown as a reusable platform rather than a hidden backend framework

## Recommended Implementation Order

### Track 1: Runtime Core

1. Phase A
2. Phase B
3. Phase C

### Track 2: Intelligence Governance

1. Phase D
2. Phase E

### Track 3: Productization

1. Phase F

## Immediate Next Step

The most important next implementation is:

1. build the true multi-agent scheduler in Phase A

Why this comes first:

- the current planner and pseudo-subagent model has reached its natural limit
- without a real scheduler, planner cannot become the central execution layer
- MCP, skills, and learning governance all benefit from a stronger parent/child runtime boundary

## Definition Of Done For The Next Iteration

The next implementation round should be considered complete only if it delivers all of the following:

1. planner item to child execution model
2. scheduler runtime service
3. fan-out / collect / merge event flow
4. backend regression coverage for success and partial failure
5. progress log update and docs index sync
