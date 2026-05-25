# Tasks: main_chat Query History Pagination

## 1. History Read Model Definition

- [x] 1.1 定义 `query_history` 与 `recent_queries` 的职责边界
- [x] 1.2 定义 history endpoint 的 response contract
- [x] 1.3 明确分页模式是 page-based、cursor-friendly，还是两者兼容

## 2. Spec Synchronization

- [x] 2.1 在 canonical spec 中补 history 层 requirement
- [x] 2.2 在 roadmap 中登记该变更为 H-2 下一刀
- [x] 2.3 在 OpenSpec README 中登记第二份真实样板

## 3. Follow-up Implementation Readiness

- [x] 3.1 明确后续实现需要变动的 backend service / router
- [x] 3.2 明确后续实现需要变动的前端消费点
- [x] 3.3 明确验证切片

## Follow-up

- [x] F1 实现 dedicated history endpoint
- [x] F2 在 `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 落最小 query history 消费壳，并验证“加载更多”链路
- [x] F3 让 Governance 侧的 history 搜索态进入视图复制/恢复链路
- [x] F4 让 Governance 侧的 history 页码进入视图复制/恢复链路
- [x] F5 增强 `MainChatQueryHistoryPanel` 的独立面板感，补齐历史指标与就地清理动作
- [x] F6 把 history 与 query detail 收进同一 workspace 布局，减少治理浏览时的上下跳转
- [x] F7 评估是否将 history 能力扩展到非 `main_chat` channel
