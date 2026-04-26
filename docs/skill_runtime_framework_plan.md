# Skill Runtime Framework Plan

## Goal

Promote skills from CRUD-managed assets into deterministic runtime participants that can be selected, injected, and audited during one agent run.

## Current Phase

### Phase D1: Runtime Selection And Injection

Implemented:

- `backend/services/skill_runtime_service.py`
  - loads enabled skills from database storage
  - parses `SKILL.md` frontmatter and body
  - scores runtime matches against:
    - user message overlap
    - `agent_role`
    - `required_capabilities`
    - direct skill-name / trigger matches
- `backend/orchestrator.py`
  - injects selected skills as runtime system prompt context
  - emits `status_kind=runtime_skills`
  - persists `runtime_skill` and `runtime_skill_effect` artifacts
- `backend/services/chat_service.py`
  - normalizes `runtime_skills` status into planner `run_trace`

### Phase D2: Priority / Activation / Conflict Policy

Implemented:

- skill frontmatter now supports lightweight runtime governance fields:
  - `priority`
  - `activation` / `activation_mode`
  - `domain`
- runtime now enforces:
  - `manual`: do not auto-select
  - `role_only`: only auto-select when `agent_role` matches
- runtime conflict resolution now suppresses overlapping candidates by deterministic policy:
  - higher runtime score wins
  - then higher `priority`
  - then stable id/name ordering

## Why This Phase Matters

The project already has planner, scheduler, MCP, and runtime trace foundations. Without runtime skill selection, the framework still behaves like it has skills as static assets instead of active runtime building blocks.

This phase establishes the minimum mature boundary:

- runtime can explain why a skill was selected
- disabled or unmatched skills do not pollute the run
- selected skills leave behind operator-readable artifacts and trace records

## Current Boundaries

Implemented now:

- deterministic runtime skill scoring
- deterministic priority / activation / conflict policy
- skill-aware system prompt injection
- planner trace visibility for runtime skill selection
- regression tests for matching and artifact persistence

Not implemented yet:

- skill as first-class callable runtime tool
- skill hit attribution in frontend operator console
- skill priority override / tenant / domain isolation
- skill approval, rollback, and governance workflow

## Next Recommended Steps

1. Bind selected skills to planner item / run records instead of prompt-only injection.
2. Promote certain skills into structured tool/context adapters instead of plain prompt excerpts.
3. Add operator-side skill hit history and run-level trace query view.
4. Extend governance to tenant / domain isolation and rollback workflow.
