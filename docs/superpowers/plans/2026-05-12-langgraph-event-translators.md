# LangGraph Event Translators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `langgraph_draft` 增加最小 `LangGraphEventTranslator` 与 `LangGraphOutputTranslator`，把外部 runtime 块映射成平台 `AgentEvent` 字典，并显式保留 `framework_adapter_status / framework_adapter_output / framework_adapter_external_error` 这三个逻辑事件语义。

**Architecture:** 继续采用 D-8 小切片策略，只扩展 `backend/agent_framework/external/langgraph_translators.py` 和对应 unittest，不改 route、不改 service、不改前端。事件翻译器只负责生成平台 `AgentEvent` 字典，trace/audit 映射仍留在后续集成切片处理。

**Tech Stack:** Python 3、unittest、现有 `AgentEventFactory / AgentEventType`

---

## 范围边界

本计划只覆盖 D-8 Slice 3：

- 新增 `LangGraphEventTranslator`
- 新增 `LangGraphOutputTranslator`
- 新增事件翻译单测

本计划明确不做：

- 不改 `FrameworkAdapterRuntimeService`
- 不改 `chat_service` 的 trace 映射
- 不新增 API route
- 不接入前端

---

## 文件结构与职责

- Modify: `backend/agent_framework/external/langgraph_translators.py`
  - 新增 `LangGraphEventTranslator`
  - 新增 `LangGraphOutputTranslator`
- Modify: `backend/agent_framework/external/__init__.py`
  - 导出两个 translator
- Create: `tests/agent_framework/test_langgraph_event_translator.py`
  - 锁定 status / reasoning / output / external_error 的最小事件形状

---

### Task 1: 先锁事件翻译 contract 测试

**Files:**
- Create: `tests/agent_framework/test_langgraph_event_translator.py`

- [ ] **Step 1: 写 status 事件测试**

```python
import unittest

from backend.agent_framework.external.langgraph_translators import (
    LangGraphEventTranslator,
    LangGraphOutputTranslator,
)


class LangGraphEventTranslatorTests(unittest.TestCase):
    def test_translate_chunk_maps_status_to_platform_status_event(self):
        translator = LangGraphEventTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_chunk(
            run_id="run_1",
            chunk={"type": "status", "status": "accepted", "detail": "runtime accepted request"},
            execution_context={"plan_id": 101},
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "status")
        self.assertEqual(events[0]["source"], "framework_adapter")
        self.assertEqual(events[0]["payload"]["adapter_id"], "langgraph_draft")
        self.assertEqual(events[0]["payload"]["framework_name"], "LangGraph")
        self.assertEqual(events[0]["payload"]["status"], "accepted")
        self.assertEqual(events[0]["payload"]["framework_adapter_event_type"], "framework_adapter_status")
```

- [ ] **Step 2: 写 reasoning 事件测试**

```python
    def test_translate_chunk_maps_reasoning_to_platform_reasoning_event(self):
        translator = LangGraphEventTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_chunk(
            run_id="run_2",
            chunk={"type": "reasoning", "summary": "planning next step", "detail": "node=planner"},
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "reasoning")
        self.assertEqual(events[0]["payload"]["framework_adapter_event_type"], "framework_adapter_reasoning")
```

- [ ] **Step 3: 写 external error 事件测试**

```python
    def test_translate_chunk_maps_error_to_platform_error_event(self):
        translator = LangGraphEventTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_chunk(
            run_id="run_3",
            chunk={
                "type": "error",
                "error_type": "connectivity_error",
                "detail": "connect failed",
            },
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "error")
        self.assertEqual(events[0]["source"], "framework_adapter")
        self.assertEqual(events[0]["payload"]["error_type"], "connectivity_error")
        self.assertEqual(
            events[0]["payload"]["framework_adapter_event_type"],
            "framework_adapter_external_error",
        )
```

- [ ] **Step 4: 写 output translator 测试**

```python
    def test_translate_final_maps_output_to_platform_content_event(self):
        translator = LangGraphOutputTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_final(
            run_id="run_4",
            output={"content": "final answer"},
            execution_context={"plan_item_id": 202},
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "content")
        self.assertEqual(events[0]["source"], "framework_adapter")
        self.assertEqual(events[0]["payload"]["content"], "final answer")
        self.assertEqual(events[0]["payload"]["framework_adapter_event_type"], "framework_adapter_output")
```

- [ ] **Step 5: 运行测试，确认当前失败**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_event_translator -v
```

Expected:

```text
ERROR: cannot import name 'LangGraphEventTranslator'
```

---

### Task 2: 实现最小事件翻译器

**Files:**
- Modify: `backend/agent_framework/external/langgraph_translators.py`
- Modify: `backend/agent_framework/external/__init__.py`
- Test: `tests/agent_framework/test_langgraph_event_translator.py`

- [ ] **Step 1: 在 translator 模块中引入事件工厂依赖**

```python
from backend.agent_framework.events import AgentEventFactory, AgentEventType
```

如果需要兼容包导入，按仓库现有风格写双路径导入。

- [ ] **Step 2: 实现 `LangGraphEventTranslator`**

实现要求：

- 构造参数：
  - `adapter_id`
  - `framework_name`
- 提供：
  - `translate_chunk(run_id, chunk, execution_context=None) -> list[dict[str, Any]]`
- 最小映射：
  - `chunk.type == "status"` -> `AgentEventType.STATUS`
  - `chunk.type == "reasoning"` -> `AgentEventType.REASONING`
  - `chunk.type == "error"` -> `AgentEventType.ERROR`
- 所有事件都必须带：
  - `source = framework_adapter`
  - `adapter_id`
  - `framework_name`
  - `execution_context`
  - `framework_adapter_event_type`

- [ ] **Step 3: 实现 `LangGraphOutputTranslator`**

实现要求：

- 构造参数：
  - `adapter_id`
  - `framework_name`
- 提供：
  - `translate_final(run_id, output, execution_context=None) -> list[dict[str, Any]]`
- 映射为：
  - `AgentEventType.CONTENT`
- payload 中至少包含：
  - `source`
  - `adapter_id`
  - `framework_name`
  - `content`
  - `execution_context`
  - `framework_adapter_event_type = framework_adapter_output`

- [ ] **Step 4: 导出两个 translator**

```python
# backend/agent_framework/external/__init__.py

from .langgraph_translators import (
    LangGraphEventTranslator,
    LangGraphOutputTranslator,
    LangGraphRequestTranslator,
)
```

- [ ] **Step 5: 运行单测，确认通过**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_event_translator -v
```

Expected:

```text
Ran 4 tests ... OK
```

---

### Task 3: 合并验证与文档衔接

**Files:**
- Modify: `docs/change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md`

- [ ] **Step 1: 在 D-8 设计稿里补 Slice 3 约束**

```md
- Slice 3 只生成平台 `AgentEvent` 字典并保留逻辑事件标记，不直接承担 trace/event_type 落库映射。
```

- [ ] **Step 2: 运行 Slice 1~3 合并验证**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator tests.agent_framework.test_langgraph_runtime_client tests.agent_framework.test_langgraph_event_translator -v
```

Expected:

```text
全部通过
```

---

## 自检结果

- Spec coverage：
  - D-8 Slice 3 的 status/output/external_error 三类最小映射都有对应任务。
- Placeholder scan：
  - 本计划未使用 `TODO / TBD / implement later / similar to task N` 这类占位表达。
- Type consistency：
  - 统一使用 `LangGraphEventTranslator.translate_chunk(...)`
  - 统一使用 `LangGraphOutputTranslator.translate_final(...)`
  - 统一使用 payload 字段 `framework_adapter_event_type`

