## Context

当前仓库已经有 `runtime-core-terms-model`、`query-run-read-model`、`governance-view-unification` 三个主规格，但它们分别从对象语义、read model、治理视图三个角度描述同一组概念。问题不是能力缺失，而是术语边界仍需要进一步一致化，否则后续新增 contract 时很容易继续写出“同一件事三种说法”。

## Goals / Non-Goals

**Goals:**
- 统一 `query / run / child_run / approval / trace / audit` 的正式定义。
- 统一 query read model 与治理视图对这些术语的解释。
- 保持对外 contract 不变，只收口语义与文案。
- 让文档、spec 和前端解释入口共享同一套语言。

**Non-Goals:**
- 不引入新的 runtime 能力。
- 不做数据库迁移或兼容层重构。
- 不改变现有 query history、query detail、governance overview 的对外字段集合。
- 不继续扩展 `main_chat` UI。

## Decisions

- 以 `runtime-core-terms-model` 作为术语真源，其他规格只做引用和收口，不再各自发明近义词。
- 以 `query-run-read-model` 作为 query / run 读模型边界真源，治理视图只解释，不重新定义。
- 以 `governance-view-unification` 作为 Runtime Surface 与 Governance Timeline 的共享解释层，避免两边分别维护语义。
- 将 `child_execution_id` 定位为兼容键，而非正式术语主键；`child_display_id` 只承担展示层稳定性。

**Alternatives considered:**
- 只改文档不改 spec: 风险是文档会继续和 contract 漂移，后续校验仍不稳定。
- 新开一套更大范围的 query workspace 规范: 过度，当前问题主要是术语收口，不是新能力设计。

## Risks / Trade-offs

- [Risk] 术语收口后，已有文档和测试的措辞需要同步。
  [Mitigation] 只改主规格和共享解释入口，保留字段与行为不变。
- [Risk] 过度强调术语统一可能让规格看起来更抽象。
  [Mitigation] 仍保留具体场景和字段锚点，避免只剩抽象定义。
- [Risk] 变更范围跨多个规格，容易产生重复表述。
  [Mitigation] 只修改三条主规格，保持一条语义链。
