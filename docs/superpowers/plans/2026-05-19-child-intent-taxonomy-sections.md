# Child Intent Taxonomy Sections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize child executor intent taxonomy and expose sectioned parent merge semantics without breaking existing consumption paths.

**Architecture:** Keep current flat merged semantics fields for compatibility, but extend the dedicated merged semantics read model with catalog metadata and explicit sections. Route all intent handling through shared normalization helpers so backend, service, router, and runtime surface all consume one stable contract.

**Tech Stack:** Python, FastAPI router/service layer, Vue 3, Vitest, unittest

---

### Task 1: Stabilize backend intent taxonomy

**Files:**
- Modify: `backend/agent_framework/sdk.py`
- Test: `tests/agent_framework/test_embedded_runtime_sdk.py`

- [ ] Add stable child intent constants and a normalize helper in `sdk.py`
- [ ] Update child execution and merge helpers to use the normalize helper instead of inline string fallback
- [ ] Add/adjust SDK tests to verify stable intent labels remain coherent

### Task 2: Add sectioned merged semantics read model

**Files:**
- Modify: `backend/agent_framework/sdk.py`
- Modify: `backend/services/runtime_surface_service.py`
- Modify: `backend/routers/health.py`
- Test: `tests/agent_framework/test_runtime_surface_service.py`
- Test: `tests/agent_framework/test_health_router.py`

- [ ] Extend `summarize_child_executor_merged_semantics(...)` with catalog metadata and `merged_sections`
- [ ] Expose the extended contract through runtime surface service and router
- [ ] Add service/router tests for the new sectioned fields

### Task 3: Update Runtime Surface consumption

**Files:**
- Modify: `frontend-vue/src/api/index.js`
- Modify: `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- Modify: `frontend-vue/src/components/ChildExecutorOutputWorkspace.vue`
- Test: `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`

- [ ] Extend the merged semantics builder to parse catalog metadata and sections
- [ ] Update the child output workspace to render sectioned parent merge results
- [ ] Keep existing summary rendering unchanged
- [ ] Add focused panel assertions for the new sectioned contract

### Task 4: Verify and document

**Files:**
- Modify: `openspec/changes/ii1-child-intent-taxonomy-sections/tasks.md`
- Modify: `docs/architecture/runtime_contracts.md`
- Modify: `docs/roadmap/next_phase_hardening.md`

- [ ] Run focused backend tests
- [ ] Run focused frontend test
- [ ] Update docs and mark the OpenSpec tasks complete
