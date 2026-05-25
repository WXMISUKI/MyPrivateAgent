# Tasks: 解耦 main_chat Query Read Model

## 1. Dedicated Endpoint

- [x] 1.1 在 `RuntimeSurfaceService` 暴露 dedicated query detail builder 入口
- [x] 1.2 在 router 中新增 `/api/runtime-profile/main-chat-query-detail`
- [x] 1.3 为 dedicated endpoint 补 focused 后端测试

## 2. Shared Frontend Contract Helper

- [x] 2.1 提取 `mainChatQueryDetail` shared helper
- [x] 2.2 让 `GovernanceTimelinePanel` 使用 dedicated endpoint + shared helper
- [x] 2.3 让 `RuntimeSurfacePanel` 使用 shared helper

## 3. Documentation Sync

- [x] 3.1 更新 `runtime_contracts.md`，明确 dedicated endpoint 的演进边界
- [x] 3.2 更新 `next_phase_hardening.md`，同步 H-2 / H-3 当前进度
- [x] 3.3 更新 `constitution.md` 与 `openspec/config.yaml`，固定 spec 驱动规则

## 4. Verification

- [x] 4.1 运行后端 `runtime_surface_service + health_router` 相关测试
- [x] 4.2 运行 `RuntimeSurfacePanel` 测试
- [x] 4.3 运行 `GovernanceTimelinePanel` 测试

## Follow-up

- [x] F1 评估 `recent_queries` 分页/历史接口
- [x] F2 评估是否为 query 级详情提供独立交互壳
- [x] F3 评估是否进一步收缩 `runtime-profile` 中的 query detail 责任
