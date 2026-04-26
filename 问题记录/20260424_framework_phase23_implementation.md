# Framework Phase 23 实施记录

## 主题
通用工具结果缓存（runtime 级）抽离

## 背景
Phase 22 已经为天气查询补了短期缓存，但那仍然是业务服务级缓存，只解决天气这一类工具。

从成熟 agent runtime 的角度看，更合理的抽象应该是：

- 由 `ToolSpec` 声明工具是否支持缓存
- 由 runtime 在执行工具前后统一读写缓存
- 业务工具只关注自己的执行逻辑

## 本次改动

### 1. 扩展 `ToolSpec`
更新 `backend/agent_framework/tools.py`：

- 新增 `cache_ttl_seconds`

用于声明工具结果缓存时间。

### 2. 新增通用工具缓存模块
新增 `backend/agent_framework/tool_cache.py`：

- `ToolResultCache`
- `get_tool_result_cache()`

能力：

- 以 `tool_name + normalized_args` 作为缓存键
- 支持 TTL 过期
- 支持全局清空
- 参数顺序无关

### 3. AgentHarness 接入缓存
更新 `backend/harness/agent_harness.py`：

- `_execute_tool()` 在工具执行前读取缓存
- 在执行成功后写入缓存
- 只有 `ToolSpec.supports_cache=True` 的工具才参与缓存
- 执行错误结果不会写入缓存

### 4. 工具元数据补充
更新 `backend/harness/tools/langchain_tools.py`：

- `search` 工具增加 `cache_ttl_seconds=300`

意味着 `search(query=...)` 的结果现在会经过 runtime 通用缓存。

## 测试

新增：

- `tests/agent_framework/test_tool_cache.py`
- `tests/agent_framework/test_agent_harness_cache.py`

并更新：

- `tests/agent_framework/test_events.py`
- `.github/workflows/ci.yml`

覆盖点：

- 参数顺序不同但逻辑相同的缓存命中
- TTL 到期后重新执行
- AgentHarness 确实命中缓存而不是重复执行工具
- `ToolSpec` 序列化包含缓存 TTL

## 验证

- `py_compile` 通过
- 新增定向测试通过
- 完整后端测试集通过

## 收益

- 缓存能力从“天气特例”提升为“runtime 通用能力”
- 后续接搜索、检索、数据库只读查询时可直接复用
- 更接近成熟智能体框架中“工具执行器负责缓存与幂等”的做法

## 下一步建议

1. 为 `tool_result` 事件增加 `cache_hit` 元数据，方便前端和日志观测
2. 继续把缓存从内存态推进到可选持久化缓存
3. 补端到端测试，覆盖缓存命中后的 `tool_result -> done` 事件链路
