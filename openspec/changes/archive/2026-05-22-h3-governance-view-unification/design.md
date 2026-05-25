## Context

`RuntimeSurfacePanel` 和 `GovernanceTimelinePanel` 已经共享了部分 query/detail 解释逻辑，但治理入口仍有分散实现：同类事件在不同面板里可能使用不同 label、不同 route mutation 方式、不同 fallback 文案。

H-3 的目标不是再造一套新的治理台，而是把已有治理入口统一成一致的 contract interpretation 和交互语义，让用户在 Runtime Surface 与 Governance Timeline 之间切换时不需要重新理解同一批概念。

## Goals / Non-Goals

**Goals:**

- 统一治理入口的 domain / filter / drill-down 语义。
- 统一 `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 对同一 contract 的解释逻辑。
- 统一 route-driven focus、snapshot focus、query focus 的命名和行为。
- 保持现有治理台布局自由度，不强行把两个面板合并成一个视图。

**Non-Goals:**

- 不新增新的治理 domain。
- 不重写 `main_chat` read model。
- 不改变后端 query/detail/history contract 的字段语义。
- 不要求两个面板在 UI 布局上完全一致。
- 不把 governance 入口扩展到非当前主线 channel。

## Decisions

### 1. Share interpretation, not layout

Reasoning:

- 统一解释逻辑可以消除漂移，但统一布局会把两个不同职责的视图绑死。
- Runtime Surface 更偏运行态概览，Governance Timeline 更偏回放与钻取，布局职责不应被强行抹平。

Alternatives considered:

- One shared mega-component: reduces duplication but destroys surface-specific ergonomics.
- Separate local helpers per panel: easier to start, but guarantees interpretation drift.

### 2. Route state is the focus state, not the object model

Reasoning:

- `governance_filter / governance_query_id / governance_snapshot / governance_dedupe_key` are observation focus keys.
- They should drive navigation and filtering, but not redefine backend entities.

Alternatives considered:

- Let route state become a parallel object model: would blur durable/runtime boundaries.

### 3. Shared normalization helpers should be narrow

Reasoning:

- The shared layer should only contain common interpretation, label mapping, and focus-state derivation.
- View-specific rendering and local UI state should remain in each component.

Alternatives considered:

- Build a large shared store/composable for everything: too coupled and harder to evolve.

### 4. Preserve current consumption boundaries

Reasoning:

- Governance views already depend on read model contracts; H-3 should make those dependencies clearer, not change them.
- Backend contracts remain the source of truth.

## Risks / Trade-offs

- [Risk] Shared interpretation may accidentally expand into view coupling. → Mitigation: limit the shared layer to contract interpretation and route/focus helpers only.
- [Risk] Surface-specific UX could be flattened. → Mitigation: keep layout and local state inside each panel.
- [Risk] Route names may still drift if undocumented. → Mitigation: document the authoritative route focus semantics and reuse them in tests.

## Migration Plan

1. Introduce or consolidate a narrow shared governance interpretation layer.
2. Move Runtime Surface and Governance Timeline to consume the same route/focus derivation.
3. Update documentation to state that route state is an observation focus, not an object model.
4. Add focused tests that assert parity across both panels for the shared concepts.

Rollback strategy:

- If the shared layer causes coupling or churn, split layout/rendering back out but keep the interpretation layer shared.
- Do not rollback the route/focus semantic contract unless absolutely necessary.

## Open Questions

- Should the shared layer live as a service module or a composable first?
- Are there any additional governance consumers that should share the same interpretation layer in the next phase?

