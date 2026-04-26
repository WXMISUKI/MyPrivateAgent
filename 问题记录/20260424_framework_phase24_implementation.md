# Framework Phase 24 实施记录

## 日期
2026-04-24

## 主题
Runtime 工具执行 Trace 与缓存可观测性增强

## 背景
Phase 23 已经把通用工具结果缓存抽到了 runtime 层，但缓存命中、工具执行耗时、结果来源仍然只存在于后端内部实现里。  
这会带来两个问题：

1. 前后端事件层无法判断工具结果来自真实执行还是缓存命中
2. artifact 和最终 `done` 事件缺少稳定的执行 trace，后续排查性能和用户体验问题成本偏高

成熟的 agent runtime 一般会把这类执行信息作为一等元数据，而不是埋在日志里。

## 本次改动

### 1. AgentRunContext 记录工具执行元数据
- 文件：`backend/agent_framework/runtime.py`
- `record_tool_result()` 新增 `execution` 字段
- tool history 现在会保留：
  - `cache_hit`
  - `duration_ms`
  - `result_source`
  - `status`

### 2. AgentHarness 补充统一工具执行 trace
- 文件：`backend/harness/agent_harness.py`
- 新增 `_execute_tool_with_metadata()`
- `_execute_tool()` 保持兼容，只返回字符串结果
- 工具执行元数据统一输出：
  - `cache_hit`
  - `duration_ms`
  - `result_source`
  - `status`

其中：
- 实时执行：`result_source=tool`
- 通用缓存命中：`result_source=runtime_cache`
- 工具缺失：`result_source=missing_tool`
- 工具异常：`result_source=tool_error`
- 等待授权：`result_source=permission_wait`

### 3. tool_result / done / artifact 对齐执行元数据
- 文件：`backend/harness/agent_harness.py`
- 文件：`backend/services/orchestrator_service.py`

现在以下对象都会携带执行 trace：
- `tool_result` 事件
- 天气等确定性结果直出时的 `content` / `done`
- `tool_result` artifact 持久化元数据

## 测试
- 更新 `tests/agent_framework/test_events.py`
- 更新 `tests/agent_framework/test_agent_harness_cache.py`
- 更新 `tests/agent_framework/test_orchestrator_service.py`

验证结果：
- 定向回归：9 项通过
- 完整后端测试：53 项通过

## 结果
这一步让框架更接近成熟 agent runtime 的可观测性标准：

- 缓存命中不再只是日志可见
- tool result 到最终 done 的执行路径可追踪
- artifact 层具备更强的复盘价值

## 下一步建议
优先继续做两件事：

1. 把 `tool_execution` 元数据透传到前端调试视图
2. 增加一条更接近真实链路的集成回归，覆盖 `tool_result -> done -> structured_card`
