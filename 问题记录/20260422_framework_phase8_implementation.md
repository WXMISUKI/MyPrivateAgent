# MyPrivateAgent 框架抽离 Phase 8 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：补齐 card schema 文档，并用 `datetime.v1` 作为第二个真实 schema 验证整套注册机制

---

## 本次实施范围

本轮不再只围绕天气，而是验证 schema 机制是否真的可扩展：

1. 新增 `datetime.v1`
2. 补齐 card schema 文档
3. 确认前后端注册、事件、组件渲染全部可复用

---

## 后端改动

### 1. 新增 card schema 工具模块

新增：

- `backend/agent_framework/card_schemas.py`

当前包含：

- `WEATHER_CARD_SCHEMA`
- `DATETIME_CARD_SCHEMA`
- `build_datetime_card_from_text()`

这样 schema 常量和解析逻辑不再散落在 Harness 或业务代码里。

### 2. 时间工具接入 schema

`backend/harness/tools/langchain_tools.py`

`get_current_datetime` 的 `ToolSpec` 已补充：

- `render_mode = structured_card`
- `card_schema = datetime.v1`

### 3. Harness 为时间工具附带 card 元数据

`backend/harness/agent_harness.py`

现在对于 `get_current_datetime`：

- 会从文本结果解析出 datetime card
- 事件中会带：
  - `card`
  - `card_schema = datetime.v1`
  - `render_mode = structured_card`

### 4. 天气 schema 常量统一化

`backend/services/weather_service.py`

天气 card 现在统一使用：

- `weather.v1`

并通过共享 schema 常量输出。

---

## 前端改动

### 1. 新增 DateTimeCard

新增：

- `frontend-vue/src/components/cards/DateTimeCard.vue`

### 2. registry 注册第二个 schema

`frontend-vue/src/components/cards/registry.js`

当前注册：

- `weather.v1 -> WeatherCard`
- `datetime.v1 -> DateTimeCard`

这说明 schema registry 已不再只服务单一类型。

---

## 文档补充

新增：

- `docs/agent_framework_card_schemas.md`

文档明确了：

1. card 基本字段
2. 事件里 `card / card_schema / render_mode` 的要求
3. 已实现 schema：
   - `weather.v1`
   - `datetime.v1`
4. 新增 schema 的扩展流程
5. schema 版本化原则

---

## 测试与验证

新增：

- `tests/agent_framework/test_datetime_cards.py`

当前 Python 测试命令：

```bash
python -m unittest tests.agent_framework.test_provider_registry tests.agent_framework.test_adapters tests.agent_framework.test_events tests.agent_framework.test_weather_cards tests.agent_framework.test_datetime_cards
```

结果：

- 10 个测试全部通过

前端验证：

- `cmd /c npm run build` 构建通过

---

## 本轮收益

1. schema 机制已经被第二个真实场景验证
2. card schema 文档化完成，后续扩展不再依赖口头约定
3. 后端 schema 常量、事件输出、前端 registry、组件渲染形成了完整闭环

---

## 当前限制

1. schema 文档还是 Markdown，不是 JSON Schema 文件
2. registry 仍是代码内静态表
3. 还没有第三类更复杂卡片验证，如检索摘要或股票

---

## 下一阶段建议

建议第九步优先做：

1. 为检索摘要或知识库结果定义第三类 schema
2. 继续把 tool result / artifact 渲染和 schema 对齐
3. 开始准备 monorepo/package 化迁移说明
