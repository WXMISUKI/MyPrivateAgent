## Context

`main_chat_query_detail` 与 `main_chat_query_history` 已经是现成的独立 read model，但它们目前更像“有字段的结果集”，而不是“自解释的契约”。在治理视图逐步后端化的阶段，这种模糊性会继续逼迫前端和审计逻辑猜测 contract 层级、来源通道和身份语义。

## Goals / Non-Goals

**Goals:**
- 为 `main_chat` query detail/history 增加稳定的契约元数据。
- 让 detail/history 自描述其 read model 层级、来源通道、身份语义和分页演进方式。
- 保持现有数据结构兼容，不引入行为破坏。
- 通过 focused tests 和文档更新把元数据变成正式真源。

**Non-Goals:**
- 不扩展新的 query workspace 能力。
- 不改变历史聚合算法或排序规则。
- 不把 `subagent_lane` 一并推广到 query history/workspace。
- 不重构前端页面，只调整其消费的 contract 语义。

## Decisions

- 采用向后兼容的 metadata 字段追加，而不是拆分出全新 contract。这样不会破坏现有 `runtime-profile` 与 dedicated endpoint 的调用方。
- 将元数据放在 `MainChatQueryReadModelBuilder` 中统一构造，避免 service 层和 router 层各自拼装语义。
- 只补 `main_chat` 的 detail/history，不顺手扩展 `subagent_lane`。这是因为当前 change 的目标是收口 query read model，而不是做 channel promotion。
- history 继续保留分页字段，并显式标注分页演进方向为 page + cursor 兼容，而不是临时枚举列表。这样后续扩展不会再让前端自己猜。

Alternatives considered:
- 新建一套完全独立的 metadata wrapper。拒绝原因：会增加一次无必要的包装层，且不符合当前兼容优先策略。
- 直接把元数据只写进文档。拒绝原因：文档不能替代运行时真源，治理视图最终仍需要可消费的 contract。

## Risks / Trade-offs

- [Low] 增加少量字段会让 contract 稍微更宽。→ 通过只加元数据、不改既有核心字段来控制变化面。
- [Low] 前端可能短期不使用这些字段。→ 仍然值得做，因为它把未来解释权从隐式约定收口成正式契约。
- [Low] snapshot 规则可能需要同步补字段。→ 用 focused tests 和 snapshot guard 一次收口。
