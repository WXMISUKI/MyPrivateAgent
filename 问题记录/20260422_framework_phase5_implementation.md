# MyPrivateAgent 框架抽离 Phase 5 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：将统一事件协议进一步落到结构化卡片渲染，先完成天气场景的 end-to-end 验证

---

## 本次实施范围

本轮选择“天气结果”作为第一个结构化卡片场景，完成：

1. 后端输出 `structured_card` 元数据
2. 前端按 `render_mode + card` 渲染卡片
3. 补充天气卡片解析测试
4. 验证前端可成功构建

---

## 后端改动

### 1. WeatherService 增加结构化卡片能力

`backend/services/weather_service.py`

新增：

- `build_weather_card(data)`
- `build_weather_card_from_text(text)`

其中：

- `build_weather_card(data)` 用于从结构化天气数据生成 card payload
- `build_weather_card_from_text(text)` 用于从稳定格式的天气文本反向解析 card

这样即使当前工具仍然返回文本，框架层也能基于稳定格式产出卡片数据。

### 2. AgentHarness 为天气结果附带 card 元数据

`backend/harness/agent_harness.py`

新增：

- `_build_tool_event_payload(...)`
- `_build_content_event_metadata(...)`

效果：

- `tool_result` 事件会带 `card`
- 确定性天气直出 `content` 事件会带：
  - `render_mode = structured_card`
  - `card = { kind: weather, ... }`
- `done` 事件也会保留对应元数据

---

## 前端改动

### 1. 事件归一化层支持 card

`frontend-vue/src/services/agentEvents.js`

新增：

- `card`

统一兼容：

- 顶层字段
- `payload.card`
- `structured_content`

### 2. Conversation Store 保存卡片状态

`frontend-vue/src/stores/conversation.js`

现在流式过程中会把：

- `assistantMessage.cardData`
- `toolCall.cardData`

保存下来，并配合：

- `renderMode`
- `toolSpec`

一起保留到最终消息状态中。

### 3. ChatView 真正渲染天气卡片

`frontend-vue/src/views/ChatView.vue`

新增：

- assistant 消息天气卡片
- tool result 天气卡片
- `structured_card` 渲染路径
- `weather-card` 相关样式

现在天气结果不再只是文本块，而是带：

- 城市
- 当前天气
- 当前气温
- 风速 / 风向
- 未来几天天气摘要

的结构化卡片。

---

## 测试与验证

新增：

- `tests/agent_framework/test_weather_cards.py`

当前 Python 测试命令：

```bash
python -m unittest tests.agent_framework.test_provider_registry tests.agent_framework.test_adapters tests.agent_framework.test_events tests.agent_framework.test_weather_cards
```

结果：

- 9 个测试全部通过

另外还完成：

1. 前端事件归一化 `node` smoke test 通过
2. 前端 `vite build` 构建通过

---

## 当前收益

1. `structured_card` 已不是概念，而是打通了一个真实高频场景
2. 后续要扩展股票、时间线、检索摘要卡片时，可以复用同一套协议
3. 前端 renderer 已从“纯 Markdown”升级为：
   - `markdown`
   - `plain_text`
   - `structured_card`

---

## 当前限制

1. 目前只对天气做了 structured card
2. card 数据仍是从稳定文本反向解析，不是工具原生返回对象
3. tool/artifact 卡片还没有统一组件化拆分

---

## 下一阶段建议

建议第六步优先做：

1. 将 structured card 提炼成通用 Vue 组件
2. 为更多确定性工具定义 card schema
3. 开始准备真正的 monorepo/package 化迁移
