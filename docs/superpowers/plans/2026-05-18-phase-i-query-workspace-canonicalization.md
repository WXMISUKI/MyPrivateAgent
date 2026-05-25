# Phase I Query Workspace Canonicalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `Phase I` 的第一批工作收口成可执行切片，优先完成 query workspace 高层真源一致性、channel promotion gate 模板和 recent summary 通用抽象判断。

**Architecture:** 本计划不继续默认扩展新 channel 实现，而是优先强化高层真源一致性与推广 gate。先完成文档/规格/roadmap 真源统一，再决定是否恢复新的 channel 级实现。

**Tech Stack:** Markdown docs, OpenSpec canonical specs, roadmap governance, FastAPI/Vue runtime architecture references

---

### Task 1: 固化 Query Workspace Canonicalization 真源

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\architecture\runtime_contracts.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\architecture\current_architecture.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\README.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\.specify\memory\constitution.md`
- Test: 轻量人工核对文档互链与术语一致性

- [x] **Step 1: 列出当前高层真源中仍可能漂移的 query workspace 表述**

检查这些关键词是否一致：

```text
recent summary
query detail
query history
query workspace
canonical baseline
channel-specific
promotion gate
```

Run:

```powershell
rg -n "recent summary|query detail|query history|query workspace|canonical baseline|channel-specific|promotion gate" docs openspec .specify
```

Expected: 能定位所有高层表述位置，为后续统一修改提供清单。

- [x] **Step 2: 收口 roadmap 中对 Phase I 的高层描述**

要求：

- `Phase I` 的任务、启动条件、收束标准与 canonical spec 一致
- 不再遗留“继续深挖 main_chat 局部体验”的默认表述

修改后关键语义应包括：

```md
- Phase I 优先收口 query workspace 通用化边界
- 多 channel 推广先过 readiness / gate
- 默认不继续扩 external_adapter 对称试点
```

- [x] **Step 3: 收口 architecture 文档中的高层真源引用**

要求：

- `current_architecture.md` 与 `runtime_contracts.md` 都明确把 `query-workspace-generalization` 视为高层真源
- `docs/README.md` 能把维护者引导到该真源

Expected: 新接手的人先看 docs 入口，就能知道 query workspace 高层边界去哪看。

- [x] **Step 4: 更新 constitution 的真源列表和工作模式描述**

要求：

- constitution 的 project truth sources 包含 `query-workspace-generalization`
- constitution 中对“先收口高层边界，再决定是否扩 channel”的模式保持一致

Expected: Spec Kit 和 OpenSpec 不会在项目真源判断上打架。

- [x] **Step 5: 轻量验收**

Run:

```powershell
rg -n "query-workspace-generalization|Phase I|promotion gate|channel-specific" docs openspec .specify
```

Expected: 术语能在 docs / roadmap / spec / constitution 四条线上互相对齐。

### Task 2: 写出 Channel Promotion Gate 模板

**Files:**
- Create: `D:\AI\AIcode\MyPrivateAgent\openspec\specs\channel-promotion-gate\spec.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\openspec\README.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Test: 轻量人工核对 gate 模板是否可复用到新 channel

- [x] **Step 1: 新建 channel promotion gate canonical spec**

目标是把“一个 channel 从 readiness 到 recent summary，再到 detail/history/workspace 的门槛”写成独立真源。

最小内容应包含：

```md
### Requirement: Promotion Gate by Layer
### Requirement: Readiness Checklist
### Requirement: Stop Condition for Over-Promotion
```

Expected: 后续新增 channel 时，不需要每次重新发明 gate 规则。

- [x] **Step 2: 把 subagent_lane / external_adapter 作为模板样例写入**

要求：

- `subagent_lane` 作为已通过 `recent summary` readiness 的样例
- `external_adapter` 作为已通过 `recent summary` readiness 但默认不继续实现的样例

Expected: 模板不是抽象空话，而是能直接映射到当前仓库事实。

- [x] **Step 3: 更新 OpenSpec README**

加入一条说明：

```md
- 如果要判断一个新 channel 能否推广 query 能力，先看 channel-promotion-gate canonical spec
```

Expected: 后续团队先看真源，再开新 change。

- [x] **Step 4: 更新 roadmap**

要求：

- 在 Phase I 里把 `channel-promotion-gate` 作为正式输入项或下一步动作
- 避免 promotion gate 仍然只停留在某一份 change 的附属内容里

Expected: `Phase I` 不再只依赖某次 change 的上下文。

- [x] **Step 5: 轻量验收**

Run:

```powershell
rg -n "channel-promotion-gate|Promotion Gate|Readiness Checklist|Over-Promotion" openspec docs
```

Expected: 新 spec 已落地，并且 README / roadmap 至少各有一个入口引用。

### Task 3: 判断 recent summary 是否值得抽象成通用 assembler

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\openspec\changes\generalize-query-workspace-boundary\design.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Optional Create: `D:\AI\AIcode\MyPrivateAgent\docs\architecture\recent_summary_abstraction_note.md`
- Test: 轻量人工核对判断结论是否能指导后续实现

- [x] **Step 1: 列出现有三类 recent summary 事实样本**

样本至少包括：

```text
main_chat_trace_overview.recent_queries
subagent_lane_recent_summary
external_adapter readiness / summary candidate
```

Expected: 后续抽象判断有真实事实基底，不是凭空设计。

- [x] **Step 2: 写出是否抽象的判断标准**

至少包含：

```md
- 字段集合是否已足够同构
- 是否会压缩掉 channel-specific 语义
- 复用收益是否高于额外抽象成本
```

Expected: 团队能据此决定“现在抽，还是继续显式复制少数 builder”。

- [x] **Step 3: 给出当前推荐结论**

推荐输出之一：

```md
- 当前先不抽通用 assembler
- 先写死共享字段集合
- 等 external_adapter recent summary 真的进入实现后，再复评
```

或者：

```md
- 当前可抽一个 very-thin summary assembler
- 只处理 shared fields，不吞并 channel-specific fields
```

Expected: 给出一个明确当前结论，而不是“以后再看”。

- [x] **Step 4: 同步 roadmap**

在 `I-3` 下写明当前判断，避免后续又回到重复讨论。

- [x] **Step 5: 轻量验收**

Run:

```powershell
rg -n "recent summary|assembler|shared fields|channel-specific fields" docs openspec
```

Expected: 至少有一处正式结论能直接回答“是否抽 recent summary 通用层”。

### Task 4: 给 Phase I 自己补 Exit Gate

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\openspec\specs\query-workspace-generalization\spec.md`
- Test: 轻量人工核对 Phase I 退出条件是否清晰

- [x] **Step 1: 明确何时允许恢复新一轮实现**

至少写清：

```md
- 高层真源是否稳定
- channel gate 是否稳定
- recent summary 抽象判断是否清晰
```

- [x] **Step 2: 明确何时继续停留在规格/架构层**

例如：

```md
- 如果新增 channel 的推广顺序还在摇摆
- 如果 canonical spec 之间仍有冲突
- 如果团队对 channel-specific / generic 的边界还没统一
```

- [x] **Step 3: 把 Exit Gate 同步进 roadmap 和 canonical spec**

Expected: `Phase I` 不会像普通 backlog 一样无限往后拖。

- [x] **Step 4: 轻量验收**

Run:

```powershell
rg -n "Exit Gate|退出条件|恢复新一轮实现|停留在规格/架构层" docs openspec
```

Expected: 至少一份 roadmap 和一份 canonical spec 直接描述 `Phase I` 的退出条件。

---

Plan complete and saved to `docs/superpowers/plans/2026-05-18-phase-i-query-workspace-canonicalization.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
