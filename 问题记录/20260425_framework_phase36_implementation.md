# Phase 36 实施记录：真实多智能体调度器第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

把当前 Planner 的伪 handoff 能力推进到第一版真实多智能体调度闭环，先完成：

1. 一个计划项拆分为多个子执行单元
2. 子执行状态持久化
3. fan-out / collect / merge 的最小运行时闭环
4. 成功与部分失败的确定性回归

## 本次实施范围

### 1. 新增 SchedulerService

- 新增文件：`backend/services/scheduler_service.py`
- 关键能力：
  - 识别一个计划项是否需要 fan-out
  - 生成 `scheduler_run_id`
  - 为子执行分配 `child_execution_id / agent_id`
  - 管理子执行状态：
    - `queued`
    - `running`
    - `completed`
    - `failed`
    - `cancelled`
  - 合并多子执行结果并输出 `merge_status`

### 2. 计划项元数据升级

- `PlanItem` 的 `metadata` 现在会记录：
  - `child_roles`
  - `child_execution_group`
  - `merge_status`
  - `merged_output`
- 这意味着当前虽然还没有独立数据库表，但已经有稳定的持久化结构可支持后续继续演进。

### 3. Planner 序列化输出补强

- 文件：`backend/services/planner_service.py`
- `serialize_plan()` 现在会补充：
  - `child_executions`
  - `merge_summary`

### 4. Chat Runtime 接入调度器

- 文件：`backend/services/chat_service.py`
- 本轮新增：
  - `scheduler_fanout_prepared`
  - `scheduler_execution`
  - `scheduler_fanout_started`
  - `scheduler_merged`
- 现在当一个计划项声明了多个角色时，聊天执行会：
  - 先准备 fan-out 子执行列表
  - 顺序执行多个子智能体上下文
  - 收集每个子执行输出
  - 最终返回一个合并后的主响应

### 5. Chat 路由接入 fan-out 执行

- 文件：`backend/routers/chat.py`
- 流式和非流式路径都已经支持：
  - 普通单子智能体执行
  - 调度器 fan-out 执行

### 6. Planner 前端展示补强

- 文件：`frontend-vue/src/components/PlannerPanel.vue`
- 当前 Planner 面板已经新增：
  - `child executions` 展示
  - `merge status` 展示
  - 子执行摘要 / 错误信息展示
  - 合并结果展示
- 这意味着调度器现在不只存在于后端数据结构中，而是能够在 demo 中被直接展示和验证。

## 新增/更新测试

### 新增

- `tests/agent_framework/test_scheduler_service.py`
  - fan-out context 生成
  - partial failure merge 行为

### 更新

- `tests/agent_framework/test_chat_service.py`
  - fan-out 调度上下文构建
- `tests/agent_framework/test_planner_service.py`
  - 计划序列化包含 `child_executions / merge_summary`
- `frontend-vue/src/components/__tests__/PlannerPanel.test.js`
  - 调度器子执行与合并状态展示

## 验证结果

执行命令：

```powershell
python -m unittest tests.agent_framework.test_planner_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

结果：

- 25 条用例全部通过
- `frontend-vue npm test`：8 个测试文件 / 25 条用例通过
- `frontend-vue npm run build`：通过

## 当前阶段价值

这一步之后，项目不再只是：

- 单计划项
- 单角色 handoff
- 单子执行上下文

而是开始具备：

- 一个计划项拆成多个角色子执行
- 子执行状态跟踪
- 子执行结果合并
- 对部分失败的可见处理

这说明 Planner 开始真正向执行调度核心靠近，而不是只做 UI 展示。

## 当前仍然存在的缺口

- 目前 fan-out 是顺序执行，不是并发调度
- 子执行还没有独立 worker/session/runtime 容器
- merge 还是规则化拼接，不是更高质量的二次汇总模型
- 还没有独立的 planner audit timeline 页面
- 还没有统一 scheduler policy / retry / approval engine

## 下一步建议

1. 给 SchedulerService 增加真正的并发 fan-out / fan-in
2. 把调度事件抽离到共享 runtime event bus
3. 给 Planner 面板增加 `child executions` 与 `merge status` 展示
4. 开始做 scheduler audit trail 和失败恢复策略
