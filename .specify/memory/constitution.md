# MyPrivateAgent Constitution

## Metadata

- Project: `MyPrivateAgent`
- Constitution Version: `1.0.0`
- Ratified Date: `2026-05-17`
- Last Amended Date: `2026-05-17`
- Scope: 本宪章用于约束 `MyPrivateAgent` 在 AI 协作开发、规格驱动开发、运行时演进、治理能力建设中的长期工程决策。

## Purpose

`MyPrivateAgent` 被定义为一个**企业内部通用智能体底座**。  
本宪章不替代架构事实文档，也不替代 roadmap；它负责约束“我们应如何开发、如何扩展、如何验证、何时停止继续优化小方向”。

本项目的架构与阶段真源如下：

1. [docs/architecture/current_architecture.md](D:/AI/AIcode/MyPrivateAgent/docs/architecture/current_architecture.md)
2. [docs/architecture/runtime_contracts.md](D:/AI/AIcode/MyPrivateAgent/docs/architecture/runtime_contracts.md)
3. [query-workspace-generalization/spec.md](D:/AI/AIcode/MyPrivateAgent/openspec/specs/query-workspace-generalization/spec.md)
4. [docs/architecture/reference_project_mapping.md](D:/AI/AIcode/MyPrivateAgent/docs/architecture/reference_project_mapping.md)
5. [docs/roadmap/next_phase_hardening.md](D:/AI/AIcode/MyPrivateAgent/docs/roadmap/next_phase_hardening.md)

如果本宪章与上述文档发生冲突，应优先修正文档，使两者重新一致，而不是让冲突长期存在。

## Article I. Runtime Core First

所有新增能力必须优先回答它属于哪一层：

- `Runtime Core`
- `Capability Layer`
- `Governance Layer`
- `Delivery Layer`

禁止事项：

- 不得把垂域业务逻辑直接写进 `Runtime Core`
- 不得让前端治理台承担后端领域判断
- 不得让某个外部框架语义反向主导我方对象模型

解释：

- 本项目的主目标不是“做一个看起来像某个产品的 UI”，而是持续收口 `run / event / approval / trace / audit / memory / skill / adapter` 这些一等对象。

## Article II. Terminology Is a Contract

术语不是文案，而是 contract 的一部分。

必须遵守：

- `query_id` 是治理观察生命周期主键
- `run_id` 是运行时执行实例主键
- `child_run_id` 是 Runtime Core 正式术语
- `child_execution_id` 仅允许留在兼容层、实现层或 repository/DB 语境

禁止事项：

- 不得在外发 contract 中对同一对象长期维持双名并存
- 不得把实现 fallback 反向定义成正式术语
- 不得让前端文案继续放大术语漂移

当出现术语漂移时，必须优先更新：

1. `docs/architecture/runtime_contracts.md`
2. 对外 contract
3. 前端展示主位
4. 测试断言

## Article III. Contract First, Frontend Second

前端是 contract 消费者，不是领域解释器。

必须遵守：

- 新增治理视图前，优先判断是否应先补后端 contract
- `Runtime Surface` 与 `Governance Timeline` 应尽量共享同一份字段解释逻辑
- 破坏性 contract 变化必须同步文档与测试

禁止事项：

- 不得为了短期展示方便，把稳定语义长期留在前端本地推导里
- 不得让多个前端组件各自维护一套相同 contract 的归一化逻辑

当前优先规则：

- 若 query 级详情可稳定后端化，则优先扩 `main_chat_query_detail`
- 若视图仍依赖临时推导，应视为过渡状态，不得当成完成态

## Article IV. Read Model Over UI Micro-Optimization

当出现“继续加卡片、加字段、加筛选器”和“继续收口 read model / contract”的选择时，默认优先后者。

必须遵守：

- 若一个方向连续 2 轮只新增展示层价值、没有新增运行时收口价值，必须暂停
- `main_chat`、`query`、`governance` 相关增强，优先沉淀成 read model

禁止事项：

- 不得在已有阶段完成线后继续无上限优化局部 UI
- 不得把 roadmap 上已明确降级的方向继续当成最高优先级

## Article V. Governance Recording Boundaries

治理记录必须有边界，不能反向破坏主执行链。

必须遵守：

- 治理记录默认遵循 `opt-in + fail-open`，除非明确属于执行安全门禁
- tool policy denied、approval gate denied 这类安全边界应 `fail-closed`
- Query Control timeline、subagent lifecycle、adapter governance 必须保持 stage/channel 可追踪

禁止事项：

- 不得因为治理写入失败而中断普通记录型执行链
- 不得把所有 metadata 都塞进 control plane

## Article VI. Spec Before Broad Change

超过单点修复范围的改动，必须先有规格，再做实现。

本项目中，满足以下任一条件时，必须先补 spec 或等价规格文档：

- 涉及 2 个及以上子系统
- 会新增或重定义 runtime contract
- 会改变术语边界或对象模型
- 会引入新的治理视图/读模型
- 会参考外部项目并吸收其架构经验

当前工具约定：

- `Spec Kit constitution`：约束项目级开发原则
- `OpenSpec`：承接功能/变更规格
- `docs/architecture/*`：承接架构真源
- `docs/roadmap/*`：承接阶段任务、当前进度、停止条件

## Article VII. Documentation Must Track Reality

文档必须随实现演进，而不是事后补录。

必须遵守：

- 新增重要 contract 时，同步更新 `runtime_contracts.md`
- 新增阶段性方向调整时，同步更新 `next_phase_hardening.md`
- 新增参考映射时，同步更新 `reference_project_mapping.md`
- 当一个改动改变维护者的入口理解时，同步更新 `docs/README.md`

禁止事项：

- 不得只改代码不改阶段判断
- 不得只改 roadmap 不改 contract 真源
- 不得让 change log 代替架构入口文档

## Article VIII. Verification Must Be Proportionate

验证必须真实，但也必须克制。

必须遵守：

- 优先运行与改动直接相关的最小测试集
- 新增 contract、helper、mapper、endpoint 时，应补 focused test
- 结论必须建立在真实验证结果上，而不是主观判断

禁止事项：

- 不得默认把重构建当成每次改动的必选项
- 不得宣称“完成/通过”但没有实际验证
- 不得留下只为临时验证而存在的测试脚手架

## Article IX. External References Are Inputs, Not Blueprints

外部项目用于校准方向，不用于直接照搬。

必须遵守：

- 参考 `learn-claude-code` 时，优先借概念边界
- 参考 `self-improving-agent` 时，优先借外挂式学习/反馈闭环
- 参考 `claude-code` 时，优先借执行壳、工具边界与治理经验

禁止事项：

- 不得为了“像某个产品”而牺牲我方 Runtime Core 一致性
- 不得直接复制外部目录结构、UI 壳或历史包袱

所有外部借鉴都应最终沉淀到：

- [docs/architecture/reference_project_mapping.md](D:/AI/AIcode/MyPrivateAgent/docs/architecture/reference_project_mapping.md)

## Operational Rules

### 1. 当前项目的推荐工作流

1. 先确认是否属于已有阶段任务
2. 若涉及较大变更，先补 OpenSpec/change spec
3. 再更新 roadmap 中的：
   - 当前状态
   - 当前进度
   - 下一步动作
   - 停止条件
4. 再进入实现与最小验证
5. 最后同步 architecture / contract 真源

### 1.1 何时必须走 OpenSpec

以下情况必须先产出 OpenSpec 规格，再进入实现：

- 新增或重定义 runtime contract
- 新增 read model、governance summary、query detail、timeline filter 之类的治理能力
- 影响 `Runtime Core / Capability / Governance / Delivery` 中两个及以上层级
- 需要吸收外部参考项目经验并落地到我方模块
- 预计会跨多个会话推进，而不是一次性完成

推荐产出内容：

- proposal：目标、边界、非目标、风险
- tasks：分步实现与验证
- archive：完成后归档变更，避免“需求已经做完但规格还悬空”

### 1.2 何时可以只走 roadmap + 直接实现

以下情况可以不单独开 OpenSpec，而是直接在现有 roadmap/architecture 约束下实现：

- 单点 bugfix
- 纯文案调整
- 已有 contract 下的局部字段显示修正
- 已有 helper / mapper / endpoint 的小范围补强，且不改变语义边界
- 直接受已有阶段任务明确覆盖、且改动可在一个会话内稳定闭环

但即便不走 OpenSpec，也必须在需要时同步：

- `docs/roadmap/next_phase_hardening.md`
- `docs/architecture/runtime_contracts.md`
- `docs/README.md`

### 1.3 当前项目的决策矩阵

| 改动类型 | 默认流程 | 必需补充 |
|---|---|---|
| 单点 bugfix / 小修 | 直接实现 | 最小验证；必要时同步 roadmap |
| contract 字段扩展 | OpenSpec + 实现 | contract 文档、测试、前端消费同步 |
| 新治理视图 / 新 read model | OpenSpec + 实现 | roadmap、contract、前端 helper |
| 术语边界调整 | 先文档收口，再实现 | `runtime_contracts.md` 真源更新 |
| 吸收外部参考经验 | 先更新 `reference_project_mapping`，再 OpenSpec | 明确借鉴点和不借鉴边界 |

### 2. 当前项目中哪些事必须先停一下再判断

出现以下情况时，必须先回到阶段判断，不得继续闷头优化：

- 正在连续优化同一个展示层局部
- 开始触碰数据库迁移或内部兼容层，而 roadmap 只要求低风险收口
- 发现同一对象在前后端文档里出现多套说法
- 外部参考开始被直接照搬，而不是先做映射判断

### 3. 规格产物最小要求

若本次改动已触发 OpenSpec，则规格至少要回答：

1. 这次改动收口的对象是什么
2. 它不收口什么
3. 它影响哪些 contract / read model / view
4. 风险点在哪
5. 完成后如何验证

如果规格里没有这些内容，应视为规格未完成，不进入实现阶段。

## Amendment Policy

- 本宪章的新增原则、原则扩张或治理流程调整，视为 `MINOR` 版本升级
- 若推翻既有核心原则或改变项目定位，视为 `MAJOR` 版本升级
- 文案澄清、错字修订、非语义性调整，视为 `PATCH` 版本升级

每次修订本宪章时，至少同步检查：

1. `AGENTS.md`
2. `docs/architecture/current_architecture.md`
3. `docs/architecture/runtime_contracts.md`
4. `docs/roadmap/next_phase_hardening.md`

## Initial Adoption Notes

当前仓库尚未完成完整 `specify init` 目录初始化；本文件先作为 `Spec Kit constitution` 第一版落地。  
后续如正式执行 `specify init --here --integration codex --script ps --force`，需先备份本文件，避免被默认模板覆盖。
