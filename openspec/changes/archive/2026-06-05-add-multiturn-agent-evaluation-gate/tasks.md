## 1. Specification

- [x] 1.1 Validate proposal/design/specs for Phase 23 Multi-turn Eval scope and non-goals.
- [x] 1.2 Confirm `multiturn-agent-evaluation-gate` uses deterministic scenario evidence and does not call live models.
- [x] 1.3 Confirm provider roadmap delta keeps behavior promotion blocked until eval scenarios pass.

## 2. Backend Contract

- [x] 2.1 Add a focused multi-turn eval gate service with JSON scenario loading.
- [x] 2.2 Support deterministic assertion groups for grounding, PromptOps, MemoryOps, tools, and response behavior.
- [x] 2.3 Return compact `passed / failed / skipped / blocked` reports.
- [x] 2.4 Keep the evaluator side-effect-free with no `/api/chat`, retrieval, prompt, memory, or tool mutation.

## 3. Scenario Fixtures

- [x] 3.1 Add a grounding-required-no-evidence scenario.
- [x] 3.2 Add a prompt-version-visibility scenario.
- [x] 3.3 Add a memory-summary-boundary scenario.

## 4. Documentation

- [x] 4.1 Update the internal control roadmap to mark MemoryOps complete and Multi-turn Eval as Phase 23 current work.
- [x] 4.2 Document the Multi-turn Eval gate in runtime contracts.
- [x] 4.3 Update the domain agent guide with eval gate usage and behavior-promotion boundary.

## 5. Verification

- [x] 5.1 Add focused tests for scenario loading, pass/fail/skipped/blocked status, and sample scenario execution.
- [x] 5.2 Run focused Multi-turn Eval tests.
- [x] 5.3 Run `openspec validate add-multiturn-agent-evaluation-gate --strict`.
- [x] 5.4 Run `openspec validate --all --strict`.

## 6. Archive

- [x] 6.1 Sync final Multi-turn Eval decisions to canonical specs.
- [x] 6.2 Archive the change after implementation tasks are complete.
