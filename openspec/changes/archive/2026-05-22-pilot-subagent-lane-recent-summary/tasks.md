# Tasks: 试点 subagent_lane recent summary

## 1. Trial Scope Definition

- [x] 1.1 定义 `subagent_lane recent summary` 的最小字段集合
- [x] 1.2 明确哪些字段本轮不允许进入
- [x] 1.3 明确后端与前端的最小候选落点

## 2. Spec Synchronization

- [x] 2.1 在 canonical spec 或 delta spec 中写清试点只到 `recent summary`
- [x] 2.2 在 roadmap 中登记其为第一个非 `main_chat` 的轻量试点候选
- [x] 2.3 在 OpenSpec README 中登记第四份样板定位

## 3. Follow-up Planning

- [x] 3.1 判断试点完成后，是否值得继续评估 `query detail`
- [x] 3.2 明确若试点失败，应该如何停在 `subagent_lane` lifecycle tracing，不继续扩展

## 4. Trial Implementation

- [x] 4.1 后端新增 `subagent_lane recent summary` dedicated contract
- [x] 4.2 路由层新增 dedicated summary endpoint
- [x] 4.3 Runtime Surface 新增最小试点入口
- [x] 4.4 补 focused 后端与前端测试

## Follow-up

- [x] F1 如试点通过，再开 `subagent-lane-query-detail-readiness` change
- [x] F2 如试点失败，回到高层边界文档，维持 `subagent_lane` 只作为 lifecycle tracing channel（已判定试点通过，因此该失败路径不执行）
