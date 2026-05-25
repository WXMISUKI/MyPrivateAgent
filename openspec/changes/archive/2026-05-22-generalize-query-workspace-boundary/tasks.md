# Tasks: 通用 Query Workspace / Query History 边界

## 1. Boundary Definition

- [x] 1.1 定义 `recent summary / query detail / query history / query workspace` 四层模型
- [x] 1.2 明确哪些层可直接推广，哪些仍然保留 `main_chat` 专用
- [x] 1.3 明确多 channel 扩展前置条件
- [x] 1.4 补 `subagent_lane / external_adapter` 当前层级判断
- [x] 1.5 补后续推荐扩展顺序

## 2. Spec Synchronization

- [x] 2.1 在 canonical spec 中补“Query Workspace Boundary” requirement
- [x] 2.2 在 roadmap 中写入当前阶段判断更新
- [x] 2.3 在 OpenSpec README 中登记这份 change 的定位

## 3. Follow-up Planning

- [x] 3.1 判断下一步是继续做通用 query workspace 设计，还是先暂停 `main_chat` 局部体验
- [x] 3.2 给后续可能的 multi-channel expansion 留出推荐顺序
- [x] 3.3 补 `subagent_lane / external_adapter` 的 readiness checklist

## Follow-up

- [x] F1 新增 `query-workspace-generalization` canonical spec
- [x] F2 评估 `subagent_lane` 是否具备进入 `recent summary` 层的前置条件
- [x] F3 评估 `external_adapter` 是否具备进入 `recent summary` 层的前置条件
- [x] F4 待其他 channel 具备 dedicated detail contract 后，再评估 `query detail` 推广（已开 `subagent-lane-query-detail-readiness` 作为 detail 前置门禁，不直接实现 detail）
- [x] F5 仅在存在明确对称验证需求时，再考虑开启 `external_adapter recent summary` 试点（当前无对称验证需求，继续暂停）
