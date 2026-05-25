# LangGraph External Pilot Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `langgraph_draft` 增加独立的 `ENABLE_LANGGRAPH_EXTERNAL_PILOT` 策略闸门，明确拆开“readiness 满足”和“允许真实 external pilot”两层语义。

**Architecture:** 继续采用 D-8 小切片策略，只修改 `backend/config.py`、`backend/agent_framework/framework_adapters.py` 和 `tests/agent_framework/test_framework_adapter_spi.py`。本切片只收紧 SPI 与策略语义，不改 service、route、doctor 或前端。

**Tech Stack:** Python 3、unittest、现有 config flag 模式、现有 `FrameworkAdapterHealth`

---

## 范围边界

本计划只覆盖 D-8 Slice 4：

- 新增 `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
- 收紧 `LangGraphDraftAdapter.can_execute()`
- 补 SPI 级回归

本计划明确不做：

- 不新增 external pilot route
- 不修改 `FrameworkAdapterRuntimeService`
- 不改前端按钮逻辑
- 不改 `StartupDiagnosticsService`

---

## 文件结构与职责

- Modify: `backend/config.py`
  - 新增 `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
- Modify: `backend/agent_framework/framework_adapters.py`
  - 让 `LangGraphDraftAdapter` 明确区分：
    - readiness ready
    - external pilot allowed
  - 覆盖 `can_execute()`，不再沿用默认实现
- Modify: `tests/agent_framework/test_framework_adapter_spi.py`
  - 锁定 readiness 与 pilot gate 的分离语义

---

### Task 1: 先锁 SPI 测试

**Files:**
- Modify: `tests/agent_framework/test_framework_adapter_spi.py`

- [ ] **Step 1: 新增“ready 但 pilot 默认关闭”测试**

```python
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_draft_adapter_ready_does_not_mean_external_pilot_allowed(self, _mock_package_available):
        adapter = LangGraphDraftAdapter()

        health = adapter.health_check().to_dict()
        can_execute, block_reason = adapter.can_execute()

        self.assertEqual(health["configuration_status"], "ready")
        self.assertEqual(health["status"], "healthy")
        self.assertFalse(can_execute)
        self.assertEqual(block_reason, "external pilot is not enabled")
```

- [ ] **Step 2: 新增“ready 且 pilot 开关开启时允许执行”测试**

```python
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_draft_adapter_allows_execution_only_when_external_pilot_enabled(self, _mock_package_available):
        adapter = LangGraphDraftAdapter()

        can_execute, block_reason = adapter.can_execute()

        self.assertTrue(can_execute)
        self.assertEqual(block_reason, "")
```

- [ ] **Step 3: 运行测试，确认当前失败**

Run:

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_spi -v
```

Expected:

```text
FAIL: ready 场景下当前实现仍返回 can_execute=True
```

---

### Task 2: 实现最小策略闸门

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/agent_framework/framework_adapters.py`
- Test: `tests/agent_framework/test_framework_adapter_spi.py`

- [ ] **Step 1: 在配置中新增 external pilot 开关**

```python
ENABLE_LANGGRAPH_EXTERNAL_PILOT = _env_flag("ENABLE_LANGGRAPH_EXTERNAL_PILOT", "false")
```

- [ ] **Step 2: 在 adapter 模块中引入新开关**

```python
from config import (
    ENABLE_LANGGRAPH_DRAFT_ADAPTER,
    ENABLE_LANGGRAPH_EXTERNAL_PILOT,
    ENABLE_LANGGRAPH_RUNTIME_EXECUTION,
    ...
)
```

包兼容导入路径也同步补齐。

- [ ] **Step 3: 覆盖 `LangGraphDraftAdapter.can_execute()`**

实现要求：

- 当 `configuration_status != "ready"`：
  - 返回 `False`
  - block reason 继续沿用 readiness 阻塞原因
- 当 `configuration_status == "ready"` 但 `ENABLE_LANGGRAPH_EXTERNAL_PILOT=false`：
  - 返回 `False`
  - block reason = `external pilot is not enabled`
- 当 `configuration_status == "ready"` 且 `ENABLE_LANGGRAPH_EXTERNAL_PILOT=true`：
  - 返回 `True`, `""`

- [ ] **Step 4: 运行 SPI 回归，确认通过**

Run:

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_spi -v
```

Expected:

```text
全部通过
```

---

### Task 3: 合并验证与文档衔接

**Files:**
- Modify: `docs/change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md`

- [ ] **Step 1: 在 D-8 设计稿里补 Slice 4 约束**

```md
- Slice 4 只在 SPI 层增加 external pilot gate，不直接开放任何真实执行入口。
```

- [ ] **Step 2: 运行 Slice 1~4 合并验证**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator tests.agent_framework.test_langgraph_runtime_client tests.agent_framework.test_langgraph_event_translator tests.agent_framework.test_framework_adapter_spi -v
```

Expected:

```text
全部通过
```

---

## 自检结果

- Spec coverage：
  - D-8 Slice 4 的核心要求“ready 不等于 external pilot allowed”已有直接测试和实现任务。
- Placeholder scan：
  - 本计划未使用 `TODO / TBD / implement later / similar to task N` 这类占位表达。
- Type consistency：
  - 统一开关名 `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
  - 统一阻断原因 `external pilot is not enabled`

