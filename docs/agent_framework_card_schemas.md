# Agent Framework 卡片 Schema 协议

## 目的

本文定义了以下模块共享的结构化卡片协议：

- 后端工具 / 运行时事件
- 前端事件归一化层
- 前端结构化卡片注册表

目标是避免页面级特殊分支，让确定性结果能够通过稳定的 schema 进行渲染。

---

## 核心规则

1. 每个结构化卡片必须包含：
   - `kind`
   - `schema`
2. `schema` 是前端分发渲染的主键。
3. `kind` 用于描述语义，但渲染器查找应优先依赖 `schema`。
4. 一个工具可以支持多个 schema；不要假设一个工具只对应一个卡片 schema。
5. 后端事件应包含：
   - `render_mode = structured_card`
   - `card`
   - `card_schema`
6. `card_schema` 应与 `card.schema` 保持一致。

---

## 事件结构

事件载荷示例：

```json
{
  "type": "content",
  "render_mode": "structured_card",
  "card_schema": "weather.v1",
  "card": {
    "kind": "weather",
    "schema": "weather.v1"
  }
}
```

---

## 已实现的 Schema

### `weather.v1`

用于天气查询结果。

示例结构：

```json
{
  "kind": "weather",
  "schema": "weather.v1",
  "city": "舟山",
  "current": {
    "weather": "小雨",
    "temperature": "15.7°C",
    "wind_speed": "22.6 km/h",
    "wind_direction": "西北"
  },
  "forecast": [
    {
      "date": "2026/04/22",
      "weather": "中雨",
      "min_temp": "14.9°C",
      "max_temp": "18.6°C",
      "precipitation": "38.9mm"
    }
  ]
}
```

### `datetime.v1`

用于当前日期 / 时间工具结果。

示例结构：

```json
{
  "kind": "datetime",
  "schema": "datetime.v1",
  "date": "2026/04/22",
  "time": "21:06:32",
  "weekday": "星期三"
}
```

### `search_summary.v1`

用于通用搜索 / 检索摘要结果。

示例结构：

```json
{
  "kind": "search_summary",
  "schema": "search_summary.v1",
  "query": "OpenAI",
  "status": "success",
  "summary": "一家人工智能公司。",
  "source": "knowledge_base",
  "source_label": "知识库",
  "source_count": 1
}
```

推荐语义：

- `source`：稳定的机器可读来源标识
- `source_label`：面向用户的来源名称
- `source_count`：实际使用或命中的具体来源数量

---

## Artifact 对齐

结构化工具结果也应作为具备 schema 感知能力的 artifact 持久化。

推荐的 artifact 字段：

- `kind`
- `content`
- `render_mode`
- `card_schema`
- `card`
- `metadata.tool_name`

这样回放、审计以及未来的 artifact UI 都可以复用与 SSE 事件一致的 schema 协议。

---

## 扩展流程

新增一个 schema 时：

1. 在后端添加 schema builder / parser
2. 如有需要，在对应工具元数据中添加 `card_schema` 或 `supported_card_schemas`
3. 在运行时事件中输出 `card` 和 `card_schema`
4. 在 `frontend-vue/src/components/cards/registry.js` 中注册该 schema
5. 添加对应渲染组件
6. 至少补充一个后端测试

---

## 版本管理

使用带版本号的 schema 名称：

- `weather.v1`
- `datetime.v1`

如果卡片结构发生不兼容变更，应创建新的 schema 版本，而不是静默修改已有版本。
