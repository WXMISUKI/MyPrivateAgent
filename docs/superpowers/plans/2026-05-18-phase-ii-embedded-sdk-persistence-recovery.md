# Phase II Embedded SDK Persistence and Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `EmbeddedAgentRuntimeSDK` 从当前 memory-first preview 推进到具备更稳恢复语义的版本，优先收口 continuation 持久化边界、恢复入口和 child executor 前置条件。

**Architecture:** 本计划不做“大一统重写”，而是先把最关键的恢复边界外提成清晰接口。优先完成 continuation/workspace 的持久化抽象与恢复 contract，再判断是否进入真实 child executor。

**Tech Stack:** Python, FastAPI service layer, Embedded SDK, Runtime Core, run metadata, contract docs, focused unittest

---

### Task 1: 定义 SDK 持久化与恢复边界

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\backend\agent_framework\sdk.py`
- Modify: `D:\AI\AIcode\MyPrivateAgent\backend\agent_framework\harness.py`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\architecture\runtime_contracts.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Test: `D:\AI\AIcode\MyPrivateAgent\tests\agent_framework\test_embedded_runtime_sdk.py`

- [x] **Step 1: 梳理当前 SDK 的易失状态边界**

至少确认这些内存态对象仍只存在于进程内：

```text
_runs
_events
_approvals
_artifacts
_tool_continuations
_loop_continuations
```

Run:

```powershell
rg -n "_runs|_events|_approvals|_artifacts|_tool_continuations|_loop_continuations" backend\agent_framework\sdk.py
```

Expected: 明确当前恢复依赖的内存态对象范围。

- [x] **Step 2: 明确第一批要抽出的持久化边界**

当前优先只定义，不一次性做全量实现：

```text
run workspace persistence boundary
tool approval continuation descriptor boundary
loop continuation descriptor boundary
artifact persistence boundary reuse
```

Expected: 先把“哪些必须抽、哪些后面再抽”写死，避免 scope 扩散。

- [x] **Step 3: 在 architecture/roadmap 中补第一版持久化边界说明**

要求：

- `runtime_contracts.md` 明确 SDK 当前 memory-first 与后续 persistence seam 的分界
- `next_phase_hardening.md` 明确 `II-1` 当前第一刀只收口 persistence/recovery 边界，不直接做全量 child executor

- [x] **Step 4: 补 focused 测试断言目标**

至少列出要验证的行为：

```text
resume_run 在 continuation descriptor 存在时能恢复
denied approval 不会留下悬空 continuation
artifact persistence 仍通过既有 ArtifactStore seam
```

- [x] **Step 5: 轻量验收**

Run:

```powershell
rg -n "continuation|ArtifactStore|resume_run|delegate_run|persistence|workspace" backend\agent_framework docs tests\agent_framework
```

Expected: 持久化与恢复边界在代码、文档、测试目标三条线上都有明确落点。

### Task 2: continuation descriptor 持久化 seam

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\backend\agent_framework\sdk.py`
- Optional Create: `D:\AI\AIcode\MyPrivateAgent\backend\agent_framework\continuations.py`
- Test: `D:\AI\AIcode\MyPrivateAgent\tests\agent_framework\test_embedded_runtime_sdk.py`

- [x] **Step 1: 提取 continuation descriptor 结构**

目标是把当前散落在 metadata 里的结构先规范化：

```python
{
  "status": "pending|consumed|discarded",
  "resume_mode": "...",
  "source": "...",
}
```

Expected: metadata 里最小字段集合统一，不再由各处手拼。

- [x] **Step 2: 让 tool continuation / loop continuation 共用稳定写入路径**

要求：

- 不改现有对外 contract 名称
- 先统一内部生成与更新逻辑

- [x] **Step 3: 为 continuation 生命周期补 focused 测试**

至少覆盖：

```text
registered
consumed
discarded
```

- [x] **Step 4: 轻量验收**

Run:

```powershell
python -m unittest tests.agent_framework.test_embedded_runtime_sdk -v
```

Expected: continuation 生命周期相关断言保持绿色。

### Task 3: 恢复入口与 child executor 前置判断

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\backend\agent_framework\sdk.py`
- Modify: `D:\AI\AIcode\MyPrivateAgent\backend\agent_framework\harness.py`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Test: `D:\AI\AIcode\MyPrivateAgent\tests\agent_framework\test_embedded_runtime_sdk.py`
- Test: `D:\AI\AIcode\MyPrivateAgent\tests\agent_framework\test_agent_harness_facade.py`

- [x] **Step 1: 明确 `resume_run(..., continue_loop=True)` 的恢复前置条件**

要求：

- 什么情况下允许恢复
- 什么情况下 fail-closed
- 什么情况下只能停留在 metadata descriptor 层

- [x] **Step 2: 明确 `delegate_run` 何时才算进入真实 child executor**

当前计划只做前置判断，不直接实现：

```text
现在：只创建 child run 与事件关系
后续：何时才允许调度真实 child execution
```

- [x] **Step 3: 把这些结论同步回 roadmap**

Expected: `II-1` 的边界足够清楚，后续不会被误解成“已经在做真实 child executor”。

- [x] **Step 4: 轻量验收**

Run:

```powershell
python -m unittest tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk -v
```

Expected: run/resume/delegate 相关契约断言保持绿色。

### Task 4: II-1 第一刀收束

**Files:**
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\roadmap\next_phase_hardening.md`
- Modify: `D:\AI\AIcode\MyPrivateAgent\docs\architecture\runtime_contracts.md`
- Optional Modify: `D:\AI\AIcode\MyPrivateAgent\openspec\README.md`

- [x] **Step 1: 写清 II-1 第一刀已完成什么**

应至少覆盖：

```text
persistence boundary clarified
continuation descriptor stabilized
resume/delegate recovery gate clarified
```

- [x] **Step 2: 写清 II-1 第一刀没有做什么**

例如：

```text
not yet full persistent workspace
not yet real child executor
not yet multi-process recovery engine
```

- [x] **Step 3: 轻量验收**

Run:

```powershell
rg -n "II-1|persistence|continuation|child executor|resume_run|delegate_run" docs openspec
```

Expected: 文档能直接回答 II-1 这一刀的完成面与边界。

---

Plan complete and saved to `docs/superpowers/plans/2026-05-18-phase-ii-embedded-sdk-persistence-recovery.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
