## Context

The control-plane sequence now has three important visibility contracts:

- Grounding Policy explains citation, ungrounded-answer, fallback, and source ACL expectations.
- PromptOps explains prompt key, version, status, template variables, eval binding, and rollback metadata.
- MemoryOps explains instruction memory, conversation summary, long-term memory posture, and retrieved-evidence non-promotion.

The remaining gap is that future behavior-affecting changes still lack a focused multi-turn regression gate. This first slice should validate scenario evidence deterministically and produce compact reports without invoking a model or changing runtime behavior.

## Goals / Non-Goals

**Goals:**

- Define a small scenario schema:
  - `id`
  - `title`
  - `turns`
  - `evidence`
  - `assertions`
  - optional `enabled` and `tags`
- Support JSON scenario files by default.
- Evaluate assertion groups for:
  - grounding policy / evidence posture
  - PromptOps prompt version/status visibility
  - MemoryOps summary and long-term-memory boundaries
  - expected tool names
  - expected response behavior labels such as `refuse_or_clarify`
- Return compact result statuses:
  - `passed`
  - `failed`
  - `skipped`
  - `blocked`
- Keep the evaluator pure and side-effect-free.

**Non-Goals:**

- No LLM call.
- No answer generation.
- No model judge.
- No CI wiring beyond focused tests.
- No frontend eval dashboard.
- No behavior promotion.

## Decisions

1. **Assertions evaluate evidence, not live model output.**
   - Decision: Scenario files include compact `evidence` blocks and expected assertions.
   - Alternative considered: Run `/api/chat` and assert generated answer text.
   - Rationale: The current goal is a stable gate contract. Live model runs would be slower, non-deterministic, and dependent on provider readiness.

2. **JSON is mandatory; YAML is optional.**
   - Decision: The loader supports `.json`; `.yaml/.yml` can be parsed if PyYAML is available.
   - Alternative considered: Require PyYAML.
   - Rationale: Avoid adding dependencies for a lightweight slice.

3. **The gate reports blocked for malformed scenarios.**
   - Decision: Missing `id`, missing turns, or invalid assertion shape returns `blocked` rather than throwing into callers.
   - Alternative considered: Let exceptions fail the whole run.
   - Rationale: Reports should be useful for operators and tests even when a scenario is incomplete.

4. **Sample scenarios live in docs.**
   - Decision: Store a few repository-owned sample scenarios under `docs/evals/multiturn/`.
   - Alternative considered: Put scenarios under tests only.
   - Rationale: These are executable examples and documentation for later teams, not just unit fixtures.

## Risks / Trade-offs

- [Risk] Deterministic evidence checks are weaker than live conversation tests. -> Mitigation: this is the first gate; live model execution and LLM judge can be separate changes after the scenario schema stabilizes.
- [Risk] Scenario evidence could drift from real runtime payloads. -> Mitigation: keep fields aligned to Grounding Policy, PromptOps, and MemoryOps contract names.
- [Risk] Teams may treat sample pass as production readiness. -> Mitigation: report metadata states `execution_mode = deterministic_contract_check`.

## Migration Plan

1. Add OpenSpec requirements.
2. Implement scenario loader and evaluator.
3. Add 2-3 sample scenarios.
4. Add focused tests for pass/fail/skipped/blocked behavior and sample scenario execution.
5. Update roadmap and docs.
6. Sync canonical specs and archive.

Rollback: remove the evaluator, sample scenarios, and docs. Existing runtime behavior remains unchanged.

## Open Questions

- Should a later live eval runner call `/api/chat`, an embedded execution facade, or a dedicated test harness?
- Should future eval reports be promoted into Runtime Contract Gate only after live execution is available?
