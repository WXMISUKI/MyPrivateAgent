# 外部参考项目映射

## 1. 目标

- 把 `learn-claude-code`、`self-improving-agent`、`claude-code` 从“讨论时的灵感源”收口成正式设计输入。
- 把 LangGraph、OpenAI Agents SDK、Qwen-Agent、CrewAI、DeerFlow、Agno 等成熟 Agent 框架收口为执行引擎参考和 adapter candidate，而不是项目级替代方案。
- 明确每个参考项目“借什么、不借什么、落到我方哪个模块”，避免后续反复回到口头比对。
- 服务于 `Phase H`，重点支持 Runtime Core、Query/Run Read Model、Governance 和扩展点设计。

## 2. 使用规则

- 参考项目只能作为边界校准与工程经验来源，不能直接照搬产品壳或目录结构。
- 若一个参考点不能清晰映射到我方 `Runtime Core / Governance Layer / Capability Layer / Delivery Layer`，默认不落地。
- 外部经验进入我方设计时，应优先转成：
  - 正式术语
  - contract 边界
  - read model
  - 扩展点/adapter 规范
- 成熟 Agent 框架进入设计时，只能作为 execution adapter、lifecycle mapping、tool/handoff/tracing 参考；不能绕过本地 Runtime Control Plane。

## 3. 参考映射表

| 项目 | 借鉴重点 | 不借鉴边界 | 我方落点模块 |
|---|---|---|---|
| `learn-claude-code` | 概念分层清晰；`task / runtime task / schedule / hook / subagent` 边界适合拿来校准我方术语；适合先做 glossary 和 contract 统一 | 不直接照搬文档叙事结构，也不把面向单一工具链的实现假设搬进来 | `docs/architecture/runtime_contracts.md`、`Runtime Core`、`Query/Run` 术语与对象模型 |
| `self-improving-agent` | 把自改进、反馈、经验沉淀做成外挂层而非侵入主执行循环；适合指导 ledger、remediation、learning pipeline 设计 | 不直接复制其自我演进策略，也不把实验性自治能力提前塞进主运行时 | `self_improvement_ledger`、`doctor / remediation`、后续 `Learning / Governance` 闭环 |
| `claude-code` | 工程化 harness、执行边界、tool/runtime 隔离、权限与审批链路、query/run 可观测性；适合继续校准执行壳与治理面 | 不追产品表象，不直接照搬 CLI/UX 或“什么都集成进一个壳”的实现策略 | `scheduler / child run / approval / run trace`、`Runtime Surface`、`Governance Timeline`、adapter/runtime contract |
| LangGraph / OpenAI Agents SDK / Qwen-Agent / CrewAI / DeerFlow / Agno | 成熟 Agent 执行框架、workflow/handoff/tool/tracing/多 agent 协作模式、adapter authoring 参考 | 不把其中任一框架作为 MyPrivateAgent 的整体替代，不直接暴露 framework-native payload 给治理台，不默认接管主 chat | `Framework Adapter`、`Query Control Plane`、`ToolRuntimeService`、`Runtime Contract Gate`、`adapter_health`、`Governance Timeline` |

## 4. 当前判断

### 4.1 当前最值得借鉴

- 先借 `learn-claude-code` 的概念边界，用于继续收口我方 `query / run / child_run / scheduler_run / approval / trace / audit`。
- 再借 `claude-code` 的工程化执行壳经验，用于收紧 runtime contract、query 级 read model 和治理入口一致性。
- `self-improving-agent` 目前更适合服务于后续学习闭环和运营型治理，而不是当前阶段的主执行内核。
- 对成熟 Agent 框架，当前最值得借的是 adapter 边界、生命周期映射、handoff/tool/tracing 证据，而不是迁移项目主体。

### 4.2 当前不建议借鉴

- 不继续把精力放在“界面像不像 Claude Code”。
- 不直接复制外部项目的目录结构、产品交互或全部模块划分。
- 不在 `Runtime Core` 尚未收口前，提前引入过重的自治/自演进逻辑。
- 不把“某个框架 star 多/大厂发布”直接等同于本项目可以取消 Runtime Control Plane。
- 不在缺少 OpenSpec adapter proposal、promotion gate 和 contract mapping 的情况下，把任何外部框架直接接入默认主 chat。

## 5. 对 Phase H 的直接作用

- `H-1`：用 `learn-claude-code` 校准概念边界，避免 Runtime Core 术语继续漂移。
- `H-2`：用 `claude-code` 的工程化经验收紧 query 级 read model，减少前端推导。
- `H-3`：让 `Runtime Surface`、`Governance Timeline`、后续治理台共享统一 query/run 语义，而不是各自解释。
- `H-4`：本文件就是参考映射的第一版正式落点，后续增量更新应继续补在这里，而不是散落在 change log 或对话里。

## 6. 当前阶段的高层收束判断

基于当前 `Phase H` 的推进情况，外部参考对我们当前阶段的最重要帮助已经从“继续补某个局部功能”切换成：

- 先判断什么能力已经可以提升成通用模式
- 再决定是否继续扩 channel

当前建议：

- `main_chat` 已经足够深，当前更像是通用 query 模式的 baseline，而不是继续默认加功能的主线。
- `subagent_lane` 与 `external_adapter` 都只先停在 `recent summary` readiness / 试点层。
- 继续扩更深层 query workspace 之前，应优先参考：
  - `learn-claude-code` 的概念边界
  - `claude-code` 的工程化执行壳经验

换句话说，当前最该借鉴的不是更多表层交互，而是：

- query/read model 的分层
- channel 推广顺序
- 何时停止继续在单一 channel 上深挖
