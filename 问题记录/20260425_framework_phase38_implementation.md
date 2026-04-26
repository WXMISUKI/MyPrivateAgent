# Phase 38 实施记录：Scheduler Timeout / Retry / Cancellation 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

给当前多智能体调度器补第一版企业级执行治理能力：

1. 子执行超时控制
2. 有界重试
3. 失败后取消剩余子任务

## 本次实施范围

### 1. Scheduler Policy 落地

- 文件：`backend/services/scheduler_service.py`
- 当前调度器已支持标准化 policy：
  - `timeout_seconds`
  - `max_retries`
  - `cancel_on_failure`
- 默认值：
  - `timeout_seconds=45`
  - `max_retries=1`
  - `cancel_on_failure=false`

### 2. 子执行状态补强

- 子执行记录现在除原有字段外，还会逐步记录：
  - `retry_count`
  - `last_retry_error`
  - `error_kind`
  - `started_at`
  - `completed_at`
  - `cancelled_at`

这意味着当前 scheduler 已经不只是“完成/失败”两态，而开始具备可审计的执行治理语义。

### 3. Chat 调度执行接入超时/重试/取消

- 文件：`backend/services/chat_service.py`
- 当前 fan-out 执行链已增加：
  - 子执行级 `asyncio.wait_for()`
  - 子执行有限重试
  - 子执行失败后按 policy 取消未完成任务

新增事件：

- `scheduler_retry`
- `subagent_cancelled`
- `scheduler_cancelled`

这使调度器在运行时开始具备“失败传播”和“策略回退”的最小能力。

## 新增/更新测试

### 更新

- `tests/agent_framework/test_scheduler_service.py`
  - 默认 policy 序列化
  - 子执行取消状态写回

- `tests/agent_framework/test_chat_service.py`
  - timeout -> retry -> failed
  - failed -> cancel remaining children
  - scheduler 事件流包含 retry / cancelled

## 验证结果

执行命令：

```powershell
python -m unittest tests.agent_framework.test_planner_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

结果：

- 29 条用例全部通过

## 当前阶段价值

现在 scheduler 已经不只是：

- 拆任务
- 跑子执行
- 合并结果

而是开始具备：

- 执行超时边界
- 失败后有限重试
- 按策略取消剩余任务
- 对应的状态沉淀与事件输出

这一步很关键，因为它把调度器从“功能性 demo”继续往“可治理 runtime”推了一层。

## 当前仍然存在的缺口

- policy 还没有从前端或 API 显式配置
- 没有统一 scheduler audit timeline
- 没有 approval checkpoint
- 没有更细的错误分类和 fallback 策略矩阵

## 下一步建议

1. 给 Planner / Settings 增加 scheduler policy 可配置入口
2. 增加 scheduler audit trail / timeline
3. 把 blocked / retry / cancel / merge 全部汇总进统一运行审计模型
