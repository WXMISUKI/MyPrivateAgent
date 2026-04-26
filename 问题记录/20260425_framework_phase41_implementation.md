# Phase 41 实施记录：Runtime Tool / MCP / Permission Run Trace 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

在上一轮统一 `run_trace` 的基础上，把聊天执行链路里的工具调用、MCP 工具调用、权限等待/拒绝事件正式接进计划项级 `run_trace`，让运行轨迹不再只覆盖 scheduler。

## 本次实施范围

### 1. Chat Runtime Trace 归一化

- 文件：`backend/services/chat_service.py`
- 新增运行时事件映射与写入逻辑：
  - `_build_run_trace_from_runtime_event()`
  - `maybe_append_runtime_run_trace()`

当前已支持从运行时事件中归一化以下 `run_trace`：

- `tool_permission_required`
- `tool_denied`
- `tool_called`
- `tool_failed`
- `mcp_tool_called`
- `mcp_tool_failed`

统一写入字段仍保持：

- `timestamp`
- `source`
- `event_type`
- `severity`
- `summary`
- `detail`
- `payload`

### 2. 三条执行路径统一接入

- 文件：`backend/services/chat_service.py`
- 文件：`backend/routers/chat.py`

当前以下执行路径都会尝试写入运行 trace：

- 普通流式聊天：`stream_orchestrator_events()`
- 普通非流式聊天：`collect_orchestrator_response()`
- 调度器并发子执行：`_run_parallel_child_execution()`

这意味着现在单智能体和 fan-out 子执行都能把工具相关运行事件回写到当前计划项。

### 3. MCP 工具调用进入统一 Trace

- 当前当运行时工具名以 `mcp_` 开头时，会被归类为 `source=mcp`
- 并按结果状态写成：
  - `mcp_tool_called`
  - `mcp_tool_failed`

这一层还没有把 MCP `probe / handshake` 面板动作接进计划项 trace，但已经先把真正影响 agent 执行结果的 MCP `tools/call` 运行事件纳入主链路。

### 4. 权限事件进入统一 Trace

- 当前权限事件会写入：
  - `tool_permission_required`
  - `tool_denied`
- `source=permission`

这让 Planner 面板里的运行轨迹开始具备“为什么执行停住”与“为什么工具没跑”的解释能力。

## 新增/更新测试

### 后端

- `tests/agent_framework/test_chat_service.py`
  - 新增流式路径回归：
    - 权限等待
    - MCP 工具调用
    - 权限拒绝
  - 新增非流式路径回归：
    - 普通工具失败写入 `tool_failed`

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_planner_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 33 条用例通过

前端：

```powershell
npm test
npm run build
```

- 8 个测试文件 / 25 条用例通过
- 构建通过

## 当前阶段价值

现在项目的统一 `run_trace` 已经不只是：

- scheduler fan-out / retry / cancel / merge
- capability blocked

而是进一步覆盖：

- 普通工具调用
- MCP runtime 工具调用
- 权限等待
- 权限拒绝

这使得 Planner 右侧面板里的执行轨迹更接近成熟智能体框架需要的“运行解释面板”。

## 当前仍然存在的缺口

- MCP `probe / handshake / tools/call` 管理页动作还没有进入计划项 trace
- 还没有 tool call start / permission approve / permission deny API 动作级 trace
- 还没有把 learning 命中、feedback 写入统一运行轨迹
- 还没有独立的 run/session 级 trace 视图与筛选器

## 下一步建议

1. 继续把 MCP `probe / handshake` 和 permission approve/deny API 动作接进统一 trace
2. 把 learning 命中、feedback、runtime artifact 命中补进 `run_trace`
3. 逐步抽离独立 `RunTraceService`，避免 trace 聚合逻辑长期堆在 `chat_service.py`
