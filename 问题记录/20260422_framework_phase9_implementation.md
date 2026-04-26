# MyPrivateAgent 框架抽离 Phase 9 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：增加第三类真实 schema，验证搜索/检索摘要卡片链路

---

## 本次实施范围

本轮新增第三类 structured card：

- `search_summary.v1`

目的是让这套框架不再只覆盖：

- weather
- datetime

而是开始进入更贴近垂域 Agent 的“检索/摘要类结果”场景。

---

## 后端改动

### 1. ToolSpec 支持多个 card schema

`backend/agent_framework/tools.py`

`ToolSpec` 新增：

- `supported_card_schemas`

这是必要的，因为像 `search` 这类工具，不应被假设只能输出一种 card。

### 2. 新增 search summary schema 生成

`backend/agent_framework/card_schemas.py`

新增：

- `SEARCH_SUMMARY_CARD_SCHEMA = search_summary.v1`
- `build_search_summary_card(query, result)`

当前会生成：

- `query`
- `status`
- `summary`

### 3. Search 工具元数据扩展

`backend/harness/tools/langchain_tools.py`

`search` 的 `ToolSpec` 现在声明支持：

- `weather.v1`
- `datetime.v1`
- `search_summary.v1`

### 4. Harness 为 search 结果生成第三类 card

`backend/harness/agent_harness.py`

对 `search` 工具结果的结构化元数据生成逻辑现在是：

1. 优先尝试 weather card
2. 再尝试 datetime card
3. 最后尝试 search summary card

这样 `search` 已开始具备“多 schema 输出能力”。

---

## 前端改动

### 1. 新增 SearchSummaryCard

新增：

- `frontend-vue/src/components/cards/SearchSummaryCard.vue`

用于展示：

- query
- status
- summary

### 2. registry 注册第三类 schema

`frontend-vue/src/components/cards/registry.js`

新增：

- `search_summary.v1 -> SearchSummaryCard`

这意味着 schema registry 已经能同时管理三种真实卡片。

### 3. schema 文档更新

`docs/agent_framework_card_schemas.md`

补充：

- `search_summary.v1`
- 一个工具可支持多个 schema 的规则

---

## 测试与验证

新增：

- `tests/agent_framework/test_search_summary_cards.py`

当前 Python 测试命令：

```bash
python -m unittest tests.agent_framework.test_provider_registry tests.agent_framework.test_adapters tests.agent_framework.test_events tests.agent_framework.test_weather_cards tests.agent_framework.test_datetime_cards tests.agent_framework.test_search_summary_cards
```

结果：

- 12 个测试全部通过

前端验证：

- `cmd /c npm run build` 构建通过

---

## 本轮收益

1. schema 机制已覆盖第三类高价值场景
2. 一个工具支持多个 schema 的路径已被验证
3. 这套框架开始更接近知识库 / 企业检索 / FAQ Agent 的复用需求

---

## 当前限制

1. search summary 目前仍然是轻量摘要卡片，不含 sources/source chunks
2. 还没有真正接入外部检索系统
3. artifact 与 structured card 之间还没有统一 schema 映射

---

## 下一阶段建议

建议第十步优先做：

1. 让 artifact 也开始对齐 schema
2. 为检索结果增加 source/source_count 等字段
3. 开始规划 monorepo/package 化目录迁移方案
