# Proposal: 收口通用 Query Workspace / Query History 边界

## Why

`main_chat` 的 query 能力已经不再只是一个简单的 trace 展示，而是逐步形成了一套完整链路：

- `recent_queries` 轻摘要
- `main_chat_query_detail` 单 query detail
- `main_chat_query_history` 长历史摘要
- `Main Chat Query Workspace` 前端治理工作区

这说明我们已经把 `main_chat` 这条线做到了“可观测、可浏览、可恢复、可分享”的阶段。

但当前还存在一个更高层的问题没有正式收口：

- 这些能力里，哪些已经可以抽成**通用 query workspace / query read model 模式**
- 哪些仍然只适合 `main_chat`
- 如果未来要支持 `subagent_lane / external_adapter / 其他 query channel`，应该复用什么，不该复用什么

如果现在不先收口边界，后面一旦扩到别的 channel，就容易再次进入：

- 每个 channel 各做一套 query history
- 前端/后端重复解释 query/detail/history 语义
- 局部功能越做越像产品壳，底座语义却越来越散

## What Changes

本次变更拟定义：

1. `query workspace` 的正式边界
2. `recent summary / query detail / query history / workspace` 四层能力的通用模型
3. 哪些能力当前可从 `main_chat` 推广
4. 哪些能力当前必须保持 `main_chat` 专用
5. 多 channel 扩展前必须满足的前置条件
6. `subagent_lane` 与 `external_adapter` 当前分别停留在哪一层
7. 后续若要推广，推荐顺序是什么

## Non-Goals

本次变更**不**直接做以下事情：

- 不直接把 query history 扩到 `subagent_lane`
- 不直接给 `external_adapter` 增加 query workspace
- 不重写当前 `main_chat` workspace 前端实现
- 不推动新的数据库迁移
- 不引入新的产品页面

## Expected Outcome

完成后应达到：

- `main_chat` 当前成果被提升为“通用 query workspace 候选模型”
- 后续若扩到其他 channel，有统一判断标准
- roadmap 不再默认把 `main_chat` 局部体验当作最高优先级
- 后续团队讨论时，不再反复争论“是不是该先给 subagent/external adapter 也做一套 history/workspace”

## Risks

1. 如果抽象过早，可能把 still-main-chat-specific 的能力误当成通用能力。
2. 如果抽象过晚，后续其他 channel 会重复造轮子。
3. 如果定义太空，会回到“写了 spec 但不能指导后续实现”的问题。

## Verification

本次规格完成后至少应能验证：

1. `main_chat` 专用能力与通用 query workspace 能力边界是否清晰
2. canonical spec 是否补出可执行的 requirement
3. roadmap 是否明确把下一阶段注意力从 `main_chat` 局部体验切回更高层的 query/read model 判断
