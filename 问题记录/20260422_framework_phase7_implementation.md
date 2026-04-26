# MyPrivateAgent 框架抽离 Phase 7 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：将 structured card 从 `kind` 级分发升级为 `card_schema` 注册机制，建立更清晰的前后端映射关系

---

## 本次实施范围

本轮聚焦“schema 注册表”这件事，而不是继续扩展更多卡片类型。

目标是让这条链路明确下来：

1. 后端事件明确给出 `card_schema`
2. 前端事件归一化保留 `card_schema`
3. 前端组件注册表按 `card_schema` 分发 renderer

---

## 后端改动

### 1. ToolSpec 支持 card_schema

`backend/agent_framework/tools.py`

`ToolSpec` 新增：

- `card_schema`

这样工具元数据已经具备承载结构化卡片 schema 的能力。

### 2. 天气 card 数据增加 schema

`backend/services/weather_service.py`

新增后，天气 card 结构中会明确携带：

- `schema: weather.v1`

并且从文本反向解析 card 时也会保留该字段。

### 3. AgentHarness 在事件中透传 card_schema

`backend/harness/agent_harness.py`

现在：

- `tool_result` 事件会带 `card_schema`
- `content` 事件会带 `card_schema`
- `done` 事件也会保留 `card_schema`

对于天气结果，当前产出的是：

- `card_schema = weather.v1`

---

## 前端改动

### 1. 新增 card registry

新增：

- `frontend-vue/src/components/cards/registry.js`

当前作用：

- 维护 `card_schema -> Vue component` 映射
- 当前注册：
  - `weather.v1 -> WeatherCard`

### 2. AgentStructuredCard 改为按 schema 分发

`frontend-vue/src/components/cards/AgentStructuredCard.vue`

原先是：

- 基于 `card.kind` 的 if/else

现在改为：

- 使用 registry 解析 `cardSchema`
- 再动态挂载对应组件

这一步很关键，因为它让后续卡片演进具备版本化能力。

### 3. 事件归一化保留 card_schema

`frontend-vue/src/services/agentEvents.js`

现在会优先读取：

- `event.card_schema`
- `payload.card_schema`
- `card.schema`
- `tool_spec.card_schema`

### 4. Conversation Store 保存 cardSchema

`frontend-vue/src/stores/conversation.js`

现在 assistant message 和 tool result 都会保留：

- `cardSchema`

### 5. ChatView 改为通过 registry 判断可渲染卡片

`frontend-vue/src/views/ChatView.vue`

不再只判断：

- `card.kind`

而是通过 registry 判断当前 schema 是否存在 renderer。

---

## 测试与验证

### Python

```bash
python -m unittest tests.agent_framework.test_provider_registry tests.agent_framework.test_adapters tests.agent_framework.test_events tests.agent_framework.test_weather_cards
```

结果：

- 9 个测试全部通过

### 前端

1. `agentEvents` smoke test 通过，确认 `card_schema` 正常归一化
2. `cmd /c npm run build` 构建通过

---

## 本轮收益

1. card 分发开始具备版本化演进能力
2. 后端工具元数据、事件协议、前端组件注册开始形成一致映射
3. 以后新增 `stock.v1`、`timeline.v1`、`retrieval_summary.v1` 时，不需要再依赖页面特判

---

## 当前限制

1. 目前只有 `weather.v1`
2. 还没有 schema 注册的共享文档或 JSON schema 文件
3. 前端 registry 还是代码内静态表，不是插件式扩展

---

## 下一阶段建议

建议第八步优先做：

1. 提炼 card schema 文档和约定
2. 为更多确定性工具定义 schema
3. 开始规划 monorepo/package 化目录迁移与发布边界
