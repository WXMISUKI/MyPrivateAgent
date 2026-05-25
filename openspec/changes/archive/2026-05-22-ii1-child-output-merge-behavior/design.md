## Context

目前 child executor 这条链已经有：

- preflight
- binding / execution / merge record
- replay
- artifact summary
- latest processing semantics UI

但 merge 语义仍然偏“最小演示版”：

- `merge_strategy` 主要还是字符串透传
- parent 侧没有真正按 child intent 分流
- replay / summary 里也还没有把“为什么这样合并”表达成正式 contract

这一步最合适的切口，不是直接上真实 child executor，而是先把 child output merge behavior 固化为正式协议。

## Goals / Non-Goals

**Goals:**

- 定义 child intent taxonomy
- 定义最小 merge modes
- 明确 replay / summary / parent metadata 三层承接面
- 为真实 child executor 提前固化 parent merge contract

**Non-Goals:**

- 不实现真实 child executor runtime
- 不实现复杂冲突解决引擎
- 不在这一步引入新的前端大面积展示扩张

## Decisions

### 1. 先收敛 intent taxonomy，再收敛 merge logic

Reasoning:

- 没有稳定 intent 分类，merge 逻辑就只能按字符串或 payload shape 猜。
- taxonomy 先稳定，后续 worker runtime 和 policy 才能围绕同一语义面工作。

### 2. 第一版只支持少量 merge modes

Reasoning:

- 现在不需要可配置策略引擎，先要一个稳定、可测试的 contract。
- 推荐先固定三类：
  - `replace_latest`
  - `append_dedup`
  - `summary_only`

### 3. parent metadata、replay、summary 三层职责分开

Reasoning:

- replay 应保留原始执行/合并轨迹
- summary 应提供消费面最小摘要
- parent metadata 只承接真正需要影响 parent state 的合并结果

## Proposed Intent Taxonomy

第一版先收敛为：

- `risk_review`
- `planning`
- `general_analysis`

后续如需扩展，再增加：

- `extraction`
- `recommendation`
- `execution_stub`

## Proposed Merge Modes

- `replace_latest`
  - 适合当前轮次最新结论覆盖旧结论
- `append_dedup`
  - 适合实体、关注点、动作建议这类可累积但需要去重的信息
- `summary_only`
  - 适合只进 replay / artifact summary，不直接写回 parent 主摘要

## First Mapping

- `risk_review`
  - `entities` -> `append_dedup`
  - `focus_points` -> `append_dedup`
  - `action_items` -> `append_dedup`
  - `latest_conclusion` -> `replace_latest`

- `planning`
  - `entities` -> `append_dedup`
  - `focus_points` -> `replace_latest`
  - `action_items` -> `replace_latest`
  - `latest_conclusion` -> `replace_latest`

- `general_analysis`
  - `entities` -> `append_dedup`
  - `focus_points` -> `summary_only`
  - `action_items` -> `summary_only`
  - `latest_conclusion` -> `replace_latest`

## Risks / Trade-offs

- [Risk] taxonomy 先天不完整。  
  Mitigation：先只支持当前已出现的 intent，后续增量扩展。

- [Risk] parent metadata 结构继续膨胀。  
  Mitigation：只写入正式 `merged_semantics`，不把 replay 细节全量塞回 parent。

- [Risk] merge mode 太少不够灵活。  
  Mitigation：先保证稳定和可解释，再决定是否需要策略插件化。

## Migration Plan

1. 定义 merge behavior helper
2. 让 child execution / merge record 带上 `intent_label / merge_behavior`
3. 让 parent metadata 写入正式 `child_executor_merged_semantics`
4. 更新 replay / summary
5. 补 focused tests 和文档

