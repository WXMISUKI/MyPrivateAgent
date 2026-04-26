# Framework Phase 10 实施记录

## 目标

在已有 `structured_card` 基础上继续收口两件事：

1. 让 `tool_result` 事件真正进入应用层与 artifact 层，而不是只停留在 Harness 内部。
2. 让 `search_summary.v1` 具备来源字段，便于后续做知识库、检索、RAG 类垂域智能体的复用。

## 本次改动

### 1. Artifact 与 Schema 对齐

- 扩展了 `backend/agent_framework/artifacts.py` 中的 `Artifact` 结构，新增：
  - `render_mode`
  - `card_schema`
  - `card`
- 更新 `backend/agent_framework/adapters.py` 中的 `InMemoryArtifactStore`，让它保存这些字段。

### 2. Orchestrator 转发并沉淀 tool_result

- 修改 `backend/orchestrator.py`
- 现在 `tool_result` 不再被丢弃，而是：
  - 原样继续向前端透传
  - 同时落入 `artifact_store`
- artifact metadata 里新增：
  - `tool_name`
  - `tool_call_id`
  - `tool_spec`
  - `model_name`
  - `source/source_label/source_count`（如果 card 中存在）

### 3. Search Summary 卡片补来源字段

- 修改 `backend/agent_framework/card_schemas.py`
- `search_summary.v1` 现在新增：
  - `source`
  - `source_label`
  - `source_count`
- 当前采用轻量推断规则：
  - 命中“知识库”字样时标记为 `knowledge_base`
  - 内置问候标记为 `builtin_runtime`
  - 其他普通检索摘要标记为 `search_tool`

### 4. 前端展示来源信息

- 修改 `frontend-vue/src/components/cards/SearchSummaryCard.vue`
- 搜索摘要卡片会显示：
  - 来源标签
  - 来源数

## 验证

- 新增 `tests/agent_framework/test_artifacts.py`
- 更新 `tests/agent_framework/test_search_summary_cards.py`

## 结果

Phase 10 后，框架在“事件协议 -> artifact 存储 -> card schema -> 前端渲染”之间形成了更一致的闭环，这比单纯增加一个卡片组件更接近可复用运行时框架的要求。
