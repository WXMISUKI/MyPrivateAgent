## Context

上一轮已经完成：

- child intent-aware merge behavior
- parent metadata 中的 `child_executor_merged_semantics`
- dedicated merged semantics read model
- Runtime Surface 对 merged semantics 的只读消费

这说明 parent merge 已经从“隐藏在 SDK 内部”进入了正式消费面。下一步更合理的是先把 intent taxonomy 和 parent sections 稳住，而不是继续扩新意图或直接上真实 executor。

## Goals / Non-Goals

**Goals**

- 固化稳定 child intent taxonomy
- 让 merged semantics read model 暴露最小 section 结构
- 保持现有前后端 contract 兼容

**Non-Goals**

- 不引入可配置 merge policy engine
- 不扩新的 child executor intent 类型
- 不在这一步实现真实 child executor runtime

## Decisions

### 1. 固化稳定 intent 常量，而不是继续依赖字符串散落

Reasoning:

- 稳定常量可以降低实现和消费面的漂移
- 后续扩 intent 时，contract 和测试入口更清楚

### 2. 保留扁平 merged semantics，同时新增 sectioned view

Reasoning:

- 现有 `latest_merged_semantics` 已经被多处消费，不能硬切
- sectioned view 更适合 parent 侧后续治理台和执行面复用

### 3. section 只表达 parent merge 结果，不重复 replay 轨迹

Reasoning:

- replay 负责轨迹
- summary 负责 child output 摘要
- merged semantics read model 负责 parent 结果解释

## Stable Intent Taxonomy

第一版固化为：

- `risk_review`
- `planning`
- `general_analysis`

并暴露：

- `intent_catalog_version`
- `supported_intents`

## Parent Merge Sections

在 dedicated merged semantics read model 中新增：

- `merged_sections.merged_entities`
- `merged_sections.merged_focus`
- `merged_sections.merged_actions`
- `merged_sections.latest_conclusion`

每个 section 至少包含：

- `section_id`
- `title`
- `merge_mode`
- `items` 或 `text`

## Migration Plan

1. 引入稳定 intent 常量和 normalize helper
2. 所有 child execution / merge 路径统一使用 normalize helper
3. 为 dedicated merged semantics read model 增加 `intent_catalog_version / supported_intents / merged_sections`
4. 补 focused tests
5. 同步 Runtime Surface 和文档
