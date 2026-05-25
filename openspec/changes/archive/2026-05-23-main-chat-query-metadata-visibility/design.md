## Context

`main_chat_query_detail` 和 `main_chat_query_history` 的解释层已经统一，但当前治理视图还没有把这层 metadata 轻量可见化。这个设计只解决一个问题：让读模型层级在现有治理面板里被明确标出来，而不是继续藏在 contract 结构里。

## Goals / Non-Goals

**Goals:**
- 轻量展示 query read model 的 metadata。
- 不改变面板骨架与交互路径。
- 让 detail/history 面板在视觉上保留统一的 contract 语义提示。
- 保持当前治理阅读体验不被打断。

**Non-Goals:**
- 不新增任何后端字段。
- 不修改 query history workspace 布局。
- 不引入新的前端状态。
- 不扩展到 subagent 或 external adapter。

## Decisions

- 在现有 detail/history 面板内增加最小 metadata 行，比起重新设计卡片布局更稳，也更容易保持当前用户习惯。
- 只展示已经统一解释出来的 metadata，不重复显示原始后端字段。这样可以继续强化“前端看的是规范化契约，不是原始 payload”。
- 不把 metadata 展示上升为新的全局 UI 模式。它只是治理视图中的契约提示，不是新的产品壳。
- 前端测试优先覆盖 metadata 是否可见，而不是追求外观断言。

Alternatives considered:
- 完全不展示 metadata。拒绝原因：虽然解释层已经统一，但缺少可见证据，治理台阅读时还需要默默相信。
- 单独做一个全局 metadata bar。拒绝原因：会引入不必要的 UI 噪音，也会和当前页面结构冲突。

## Risks / Trade-offs

- [Low] 页面信息密度增加一点。→ 只增加轻量文本，不扩展布局块。
- [Low] 用户可能短期不关注 metadata。→ 仍然值得保留，因为它是治理语义的显式提示。
- [Low] 测试会更关注文案。→ 这是可接受的，因为这里本来就是 contract 可见性。
