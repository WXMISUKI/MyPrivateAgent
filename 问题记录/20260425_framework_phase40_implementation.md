# Phase 40 实施记录：Unified Run Trace 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

在现有 `scheduler audit trail` 的基础上，补一层统一 `run_trace`，让计划执行、能力阻塞、调度取消等关键运行事件具备一致的数据结构与前端展示入口。

## 本次实施范围

### 1. Scheduler 统一 Run Trace 能力

- 文件：`backend/services/scheduler_service.py`
- 新增统一 trace 读写方法：
  - `get_run_trace()`
  - `append_run_trace_event()`
- 当前 `run_trace` 记录结构统一为：
  - `timestamp`
  - `source`
  - `event_type`
  - `severity`
  - `summary`
  - `detail`
  - `payload`

目前已纳入统一 `run_trace` 的事件包括：

- `scheduler_fanout_prepared`
- `scheduler_execution_started`
- `child_running`
- `child_completed`
- `child_failed`
- `child_retrying`
- `child_cancelled`
- `scheduler_merged`
- `scheduler_cancelled`
- `capability_blocked`

### 2. Planner API 序列化补强

- 文件：`backend/services/planner_service.py`
- 文件：`backend/schemas.py`
- `PlanItemResponse` 现在新增返回：
  - `run_trace`

这意味着当前一个计划项除了保留历史 `audit_trail` 外，也开始具备统一运行轨迹视图。

### 3. Chat Runtime 事件接入

- 文件：`backend/services/chat_service.py`
- 当前以下运行时场景会写入统一 trace：
  - 计划项所需 capability 缺失或不可用时，写入 `capability_blocked`
  - 开启 `cancel_on_failure` 后调度取消剩余子执行时，写入 `scheduler_cancelled`

这一步把“调度审计”和“运行时阻塞/取消”第一次接到了同一条 trace 链路上。

### 4. Planner 前端 Run Trace 展示

- 文件：`frontend-vue/src/components/PlannerPanel.vue`
- 新增“运行 Trace”区块
- 当前可展示：
  - 事件来源
  - 事件类型
  - 时间
  - 摘要
  - 详情

前端现在不只可看子执行时间线，也可以直接看统一的运行轨迹。

## 新增/更新测试

### 后端

- `tests/agent_framework/test_scheduler_service.py`
  - 新增 `append_run_trace_event()` 相关回归

- `tests/agent_framework/test_planner_service.py`
  - 补充 `serialize_plan()` 返回 `run_trace` 的断言

- `tests/agent_framework/test_chat_service.py`
  - 对应测试桩补齐 `append_run_trace_event()`

### 前端

- `frontend-vue/src/components/__tests__/PlannerPanel.test.js`
  - 增加统一 `run_trace` 展示断言

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_planner_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 31 条用例通过

前端：

```powershell
npm test
npm run build
```

- 8 个测试文件 / 25 条用例通过
- 构建通过

## 当前阶段价值

现在项目的可观测性不再只停留在：

- 计划项时间线
- scheduler 局部审计

而是开始形成统一的运行轨迹模型。这对后续继续整合：

- MCP 调用审计
- 工具调用链路
- 学习命中/反馈事件
- operator 级 run trace 查询

都有直接价值。

## 当前仍然存在的缺口

- `run_trace` 目前仍主要覆盖 scheduler 与 capability 事件
- 还未统一纳入 MCP `probe / handshake / tools/call`
- 还未纳入 tool call / permission / feedback / learning 命中
- 还没有单独的运行追踪页和筛选器

## 下一步建议

1. 继续把 MCP、tool call、permission 事件接入统一 `run_trace`
2. 给前端增加更完整的 trace 展开、筛选和复制能力
3. 再考虑将 `run_trace` 提升为独立 run/session 级视图
