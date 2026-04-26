# Phase 42 实施记录：Permission Approval Run Trace 与 Router 级 Trace Service

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

继续完善统一 `run_trace`，把聊天执行期之外、但仍直接影响 agent 执行的审批动作纳入可追踪范围，并抽出可复用的 router 级 trace 追加服务。

## 本次实施范围

### 1. 新增 Router 级 RunTraceService

- 文件：`backend/services/run_trace_service.py`
- 新增 `RunTraceService`
- 当前提供：
  - `append_latest_active_item_trace()`

作用：

- 允许非聊天主链路的 service / router 也能安全地把事件追加到“当前会话最新计划的活动计划项”
- 避免继续把 trace 聚合逻辑全部堆在 `chat_service.py`

这一步是后续继续把 MCP 管理动作接进 trace 的基础。

### 2. 权限审批动作进入统一 Run Trace

- 文件：`backend/routers/permissions.py`
- `approve_permission()` 现在会追加：
  - `source=permission`
  - `event_type=permission_approved`
- `deny_permission()` 现在会追加：
  - `source=permission`
  - `event_type=permission_denied`

写入内容包括：

- `request_id`
- `tool_name`
- `tool_args`
- 审批结果

这意味着当前 Planner / Timeline 视角已经不只是能看到“工具等待授权”和“工具被拒绝执行”，也能看到“用户什么时候真正批准/拒绝了请求”。

### 3. PermissionService 恢复能力增强

- 文件：`backend/harness/permission_service.py`
- `approve()` / `deny()` 现在在内存态未命中时，会回退读取持久化记录

价值：

- 避免服务重启后，审批接口因为请求只存在数据库而直接失败
- 让审批链路更接近企业级可恢复行为

## 新增/更新测试

### 后端

- `tests/agent_framework/test_run_trace_service.py`
  - 验证可将 trace 追加到当前活动计划项
  - 验证计划缺失时返回 `False`

- `tests/agent_framework/test_permissions_router.py`
  - 验证 `approve_permission()` 会写入 `permission_approved`
  - 验证 `deny_permission()` 会写入 `permission_denied`

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_permissions_router tests.agent_framework.test_run_trace_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_planner_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 37 条用例通过

## 当前阶段价值

现在统一 `run_trace` 已经覆盖三类关键范围：

- 调度器执行轨迹
- 工具 / MCP 工具 / 权限等待与拒绝
- 权限审批 API 动作本身

也就是说，项目开始具备“从等待授权到最终批准/拒绝”的完整审批追踪链。

## 当前仍然存在的缺口

- MCP 管理页上的 `probe / handshake / tools/call` 诊断动作还未接入统一 trace
- learning 命中、feedback、runtime artifact 仍未进入统一 trace
- `RunTraceService` 当前只支持“最新活动计划项”追加，还没有 run/session 级聚合视图

## 下一步建议

1. 继续把 MCP router 的 `probe / handshake / tools/call` 动作接入 `RunTraceService`
2. 给 `RunTraceService` 增加“按 conversation / run 查询”的统一读取接口
3. 再把 learning / feedback 事件纳入统一 trace 模型
