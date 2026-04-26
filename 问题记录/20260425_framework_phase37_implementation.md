# Phase 37 实施记录：并发 Fan-Out 调度第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

把 Phase 36 的顺序 fan-out 调度推进到第一版并发 fan-out，使多子智能体执行更接近真实调度器。

## 本次实施范围

### 1. 调度执行改为并发收集

- 文件：`backend/services/chat_service.py`
- 关键改动：
  - `stream_scheduled_orchestrator_events()` 不再顺序执行每个 child context
  - 改为为每个 child context 创建独立异步任务
  - 使用 `asyncio.as_completed()` 收集已完成子执行
  - 子执行结果在主调度循环里统一落状态和发事件

### 2. 子执行使用独立 orchestrator 实例

- 新增 `_get_orchestrator_factory()`
- 新增 `_run_parallel_child_execution()`
- 每个子执行现在都会创建自己的 orchestrator 实例，而不是复用同一个 orchestrator

这一步的意义是：

- 子执行之间开始具备真正的并发边界
- 后续继续升级成独立 worker / session / runtime 时，接口边界已经更合理

### 3. 调度事件语义更新

- `scheduler_fanout_started` 现在明确表示：
  - 开始并发执行多个子智能体任务
- `subagent_spawned / subagent_collected / subagent_failed / scheduler_merged`
  继续保留，便于前端和后续 audit 直接消费

## 新增/更新测试

- 更新：`tests/agent_framework/test_chat_service.py`
  - 新增并发调度流测试
  - 验证：
    - `scheduler_fanout_started`
    - `subagent_spawned`
    - `subagent_collected`
    - `scheduler_merged`
    - 合并结果确实回流为最终输出

## 验证结果

执行命令：

```powershell
python -m unittest tests.agent_framework.test_planner_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

结果：

- 26 条用例全部通过

## 当前阶段价值

现在项目已经不只是：

- 计划项拆分为多个子执行
- 顺序调用多个子上下文

而是开始具备：

- 多个子执行单元并发运行
- 按完成顺序收集结果
- 统一合并为主响应

这使调度层更接近真正的 fan-out / fan-in，而不是“for 循环串行调用”。

## 当前仍然存在的缺口

- 仍然没有独立进程/线程级 worker 隔离
- 没有 scheduler 级 retry / cancellation / timeout policy
- 没有 planner timeline / audit 面板
- 没有统一 approval / fallback policy

## 下一步建议

1. 给 scheduler 增加 timeout / retry / cancellation 策略
2. 加 scheduler audit trail 和 planner timeline
3. 把并发调度事件进一步抽离到共享 runtime event bus
