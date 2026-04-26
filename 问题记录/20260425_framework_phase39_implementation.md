# Phase 39 实施记录：Scheduler Audit Trail 与 Planner Timeline 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

给当前调度器补第一版可观测性能力，让多智能体执行不只是“有状态”，而且“可回看、可解释、可展示”。

## 本次实施范围

### 1. Scheduler Audit Trail 落地

- 文件：`backend/services/scheduler_service.py`
- 当前每个计划项都会在 `metadata.audit_trail` 中沉淀时间线事件
- 已覆盖的事件包括：
  - `scheduler_fanout_prepared`
  - `scheduler_execution_started`
  - `child_running`
  - `child_completed`
  - `child_failed`
  - `child_retrying`
  - `child_cancelled`
  - `scheduler_cancelled`
  - `scheduler_merged`

每条审计记录包含：

- `timestamp`
- `event_type`
- `content`
- `payload`

### 2. Planner API 序列化补强

- 文件：`backend/services/planner_service.py`
- `PlanItemResponse` 现在会额外返回：
  - `audit_trail`

### 3. Planner Timeline 前端展示

- 文件：`frontend-vue/src/components/PlannerPanel.vue`
- 当前 Planner 面板已经新增：
  - 执行时间线区块
  - 倒序展示最近审计事件
  - 展示事件标签、时间、说明

这意味着当前 demo 已经能直接展示：

- 为什么拆分
- 谁开始执行
- 谁失败了
- 谁重试了
- 为什么取消
- 什么时候完成合并

## 新增/更新测试

### 后端

- `tests/agent_framework/test_scheduler_service.py`
  - `append_audit_event()`
  - `get_audit_trail()`

- `tests/agent_framework/test_planner_service.py`
  - `serialize_plan()` 包含 `audit_trail`

### 前端

- `frontend-vue/src/components/__tests__/PlannerPanel.test.js`
  - 调度时间线展示

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_planner_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 30 条用例通过

前端：

```powershell
npm test
npm run build
```

- 8 个测试文件 / 25 条用例通过
- 构建通过

## 当前阶段价值

现在项目已经不只是：

- 会拆计划
- 会调度子执行
- 会重试和取消

而是开始具备：

- 计划项级运行审计
- 前端可见的执行时间线
- 对调度行为的最小解释能力

这一步让项目进一步接近成熟智能体框架的“可观测执行”体验。

## 当前仍然存在的缺口

- 时间线还只是计划项局部视图，不是完整 run trace
- 没有统一跨 planner / tool / MCP / learning 的审计模型
- 没有独立 timeline 页面或筛选能力
- 还没有 operator 级搜索与导出

## 下一步建议

1. 把 scheduler audit 与 MCP / tool / learning 事件汇总成统一 run trace
2. 增加 planner timeline 的筛选、展开详情和导出能力
3. 开始给 scheduler policy 增加前端可配置入口
