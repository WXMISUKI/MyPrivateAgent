# Framework Phase 22 实施记录

## 主题
天气工具短期缓存与关键链路回归测试补充

## 背景
在最近的天气查询问题中，系统主要瓶颈已经不再是工具调用协议，而是外部天气 API 的网络波动。

即使工具链路正确，重复查询同一个城市时仍然会：

- 重复访问 Open-Meteo
- 受网络抖动影响
- 拉高整体响应时间

因此，这一阶段的重点是为确定性强、更新频率不高的天气查询补短期缓存，并把缓存行为纳入回归测试。

## 本次改动

### 1. 天气服务增加短期缓存
更新 `backend/services/weather_service.py`：

- 新增 `cache_ttl_seconds`
- 新增 `_weather_cache`
- 新增 `_get_cached_weather()`
- 新增 `_store_cached_weather()`
- 新增 `clear_cache()`
- 新增 `_fetch_weather_payload()`，将网络访问抽成独立方法

行为：

- 默认缓存 TTL 为 `300s`
- 同一城市在 TTL 内重复查询，直接命中缓存
- 过期后自动重新拉取
- 返回值使用深拷贝，避免调用方污染缓存对象

### 2. 补充缓存测试
新增 `tests/agent_framework/test_weather_service_cache.py`，覆盖：

- 同城重复查询命中缓存
- 缓存对象不被调用方修改污染
- TTL 到期后重新拉取

### 3. CI 纳入缓存测试
更新 `.github/workflows/ci.yml`，将新测试纳入后端 runtime 测试集合。

## 验证

- `py_compile` 通过
- `tests.agent_framework.test_weather_cards` 通过
- `tests.agent_framework.test_weather_service_cache` 通过
- 完整后端测试集通过

## 收益

- 天气查询在短时间内重复提问时明显更稳
- 对外部天气 API 网络波动更不敏感
- 为后续把缓存扩展到搜索摘要、时间类工具打了基础

## 下一步建议

1. 把缓存命中信息做成更明确的 debug 日志
2. 将工具缓存抽成通用 `tool result cache`，而不仅是天气专用缓存
3. 补浏览器端或 API 级端到端测试，覆盖 `tool_result -> done -> structured_card` 全链路
