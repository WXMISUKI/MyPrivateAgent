## Why

MyPrivateAgent now has visible Grounding Policy, PromptOps, and MemoryOps contracts, but behavior-affecting promotion still lacks a small repeatable multi-turn regression gate. Before default RAG injection, prompt activation, or memory injection can be promoted, the project needs deterministic scenario checks that prove the relevant contract evidence is present and interpretable.

收口对象：多轮场景文件格式、deterministic eval gate、compact report、后续行为 promotion 前的最小验收门禁。非目标：不做完整 eval 平台、不接 LLM-as-judge、不启动默认 RAG 注入、不做 PromptOps rollout、不写长期记忆。

## What Changes

- Add a `multiturn-agent-evaluation-gate` capability for scenario-based regression over prompt, grounding, memory, tool, and refusal/fallback expectations.
- Add a lightweight backend evaluator that loads JSON/YAML-like scenario files and evaluates deterministic assertions against supplied evidence blocks.
- Add a small local scenario set covering no-evidence grounding, prompt version visibility, and memory summary boundaries.
- Produce compact scenario reports with `passed / failed / skipped / blocked` statuses.
- Update roadmap and runtime docs to mark MemoryOps complete and Multi-turn Eval as Phase 23 current work.
- Non-goals:
  - Do not call a real LLM.
  - Do not implement LLM-as-judge or dataset management.
  - Do not change `/api/chat`, prompt injection, context packing, retrieval, or tool execution behavior.
  - Do not require the external RAG / GraphRAG provider to be ready.

## Capabilities

### New Capabilities

- `multiturn-agent-evaluation-gate`: Defines the minimal scenario schema, deterministic assertions, and compact eval gate report.

### Modified Capabilities

- `provider-capability-roadmap`: Records that multi-turn eval gate is the next internal control-plane slice before behavior-affecting prompt/RAG/context promotion.

## Impact

- Affected backend contracts:
  - New focused evaluation service.
  - Local scenario fixtures under docs/evals or equivalent repository-owned location.
- Affected docs:
  - `docs/roadmap/internal_agent_control_tasks_2026-06-03.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/guides/domain_agent_development_guide.md`
- Affected tests:
  - focused backend tests for scenario loading, assertion results, status rollup, and sample scenario execution.
- Dependencies:
  - No new runtime dependency.
  - Optional YAML parsing may be used only if available; JSON must be supported by default.
