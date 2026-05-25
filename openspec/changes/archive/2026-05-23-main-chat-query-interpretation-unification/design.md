## Context

`main_chat_query_detail` 与 `main_chat_query_history` 已经成为后端 read model 的正式真源，但前端当前仍存在多处组件级消费与 fallback 推导。设计目标不是再发明一层抽象，而是把解释口径收束到一条共享路径，避免 Runtime Surface 与 Governance Timeline 对同一 contract 产生不同理解。

## Goals / Non-Goals

**Goals:**
- 统一 query detail/history 的 normalize 结果。
- 让 detail/history 的自描述 metadata 在前端解释层被显式保留。
- 保持现有治理页面交互与视觉不变。
- 减少组件级 fallback 推导带来的语义漂移。

**Non-Goals:**
- 不新增新的 query workspace 能力。
- 不调整后端分页、排序或过滤算法。
- 不重构治理页面布局。
- 不把 subagent/external adapter 的 history 解释一并推广。

## Decisions

- 采用共享 helper 收口，而不是在每个组件里重复 normalize。这样 `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 使用的是同一份解释语义。
- 让 `mainChatQueryReadModel` 继续承担 normalize 入口，并补足 metadata 字段透传，避免在业务组件里直接读原始 contract。
- 仅统一 `main_chat` 的 detail/history 解释，不扩展到其他 channel。原因是当前 change 的目标是治理视图一致性，不是 channel promotion。
- 不引入新依赖或状态容器。共享解释层已经存在，新增抽象只会增加维护成本。

Alternatives considered:
- 在组件里分别兼容 metadata。拒绝原因：会加重重复逻辑，无法真正保证语义一致。
- 把解释逻辑下沉到 Pinia store。拒绝原因：这是读模型解释，不是业务状态管理。

## Risks / Trade-offs

- [Low] 前端 helper 输出字段会更多。→ 通过保持核心字段不变、只追加 metadata 来控制。
- [Low] 一些组件可能暂时不展示 metadata。→ 仍然有价值，因为它们可以在统一 normalize 结果中消费。
- [Low] 旧测试可能依赖旧默认值。→ 用 focused tests 先锁定统一 contract，再补展示断言。
