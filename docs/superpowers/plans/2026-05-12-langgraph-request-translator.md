# LangGraph Request Translator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `langgraph_draft` 增加独立的 `LangGraphRequestTranslator`，把平台 `run_id / messages / execution_context` 收口成稳定、可测试、与外部 runtime client 解耦的最小请求形状。

**Architecture:** 采用最小切片策略，只落 `translator` 模块与对应单测，不接网络、不改 `FrameworkAdapterRuntimeService`、不改现有 `precheck` 或 fake pilot。translator 放到新的 `backend/agent_framework/external/` 目录中，作为后续 `LangGraphRuntimeClient / EventTranslator / External Pilot` 的基础依赖。

**Tech Stack:** Python 3、unittest、现有 `backend.agent_framework` SPI 与 DTO 约定

---

## 范围边界

本计划只覆盖 D-8 Slice 1：

- 新建 `external/` 目录
- 新建 `LangGraphRequestTranslator`
- 新建 request shape 单测

本计划明确不做：

- 不发真实 HTTP 请求
- 不新增 route
- 不修改 `LangGraphDraftAdapter.can_execute()`
- 不接入 trace / audit
- 不新增前端行为

---

## 文件结构与职责

- Create: `backend/agent_framework/external/__init__.py`
  - 暴露 `LangGraphRequestTranslator`
- Create: `backend/agent_framework/external/langgraph_translators.py`
  - 定义 `LangGraphRequestTranslator`
  - 负责消息标准化、execution context 白名单化、最小请求 dict 构造
- Create: `tests/agent_framework/test_langgraph_request_translator.py`
  - 锁定 translator 输出 shape
  - 锁定 role / content 归一化
  - 锁定 execution context 兼容策略

---

### Task 1: 建立 translator 测试基线

**Files:**
- Create: `tests/agent_framework/test_langgraph_request_translator.py`

- [ ] **Step 1: 先写失败测试，锁定最小 request shape**

```python
import unittest

from backend.agent_framework.external.langgraph_translators import LangGraphRequestTranslator


class LangGraphRequestTranslatorTests(unittest.TestCase):
    def test_translate_builds_stable_langgraph_request_shape(self):
        translator = LangGraphRequestTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            assistant_id="draft-assistant",
            endpoint="http://localhost:8000/langgraph",
        )

        payload = translator.translate(
            run_id="run_123",
            messages=[
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "world"},
            ],
            execution_context={
                "plan_id": 101,
                "plan_item_id": 202,
                "run_kind": "framework_adapter",
                "ignored_field": "should_not_leak",
            },
        )

        self.assertEqual(payload["adapter_id"], "langgraph_draft")
        self.assertEqual(payload["framework_name"], "LangGraph")
        self.assertEqual(payload["run_id"], "run_123")
        self.assertEqual(payload["assistant_id"], "draft-assistant")
        self.assertEqual(payload["endpoint"], "http://localhost:8000/langgraph")
        self.assertEqual(
            payload["messages"],
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "world"},
            ],
        )
        self.assertEqual(
            payload["execution_context"],
            {
                "plan_id": 101,
                "plan_item_id": 202,
                "run_kind": "framework_adapter",
            },
        )
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator -v
```

Expected:

```text
ERROR: No module named 'backend.agent_framework.external'
```

- [ ] **Step 3: 补第二个失败测试，锁定消息归一化**

```python
    def test_translate_normalizes_message_role_and_content(self):
        translator = LangGraphRequestTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            assistant_id="draft-assistant",
            endpoint="http://localhost:8000/langgraph",
        )

        payload = translator.translate(
            run_id="run_456",
            messages=[
                {"role": "USER", "content": "  hi  "},
                {"content": "missing role defaults to user"},
                {"role": "", "content": None},
            ],
            execution_context={},
        )

        self.assertEqual(
            payload["messages"],
            [
                {"role": "user", "content": "hi"},
                {"role": "user", "content": "missing role defaults to user"},
                {"role": "user", "content": ""},
            ],
        )
```

- [ ] **Step 4: 再次运行测试，确认仍失败但用例已锁定**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator -v
```

Expected:

```text
FAILED (errors=2)
```

- [ ] **Step 5: 提交测试基线**

```bash
git add tests/agent_framework/test_langgraph_request_translator.py
git commit -m "test: lock langgraph request translator contract"
```

---

### Task 2: 实现 translator 最小骨架

**Files:**
- Create: `backend/agent_framework/external/__init__.py`
- Create: `backend/agent_framework/external/langgraph_translators.py`
- Test: `tests/agent_framework/test_langgraph_request_translator.py`

- [ ] **Step 1: 新建 external 包导出 translator**

```python
# backend/agent_framework/external/__init__.py

from .langgraph_translators import LangGraphRequestTranslator

__all__ = ["LangGraphRequestTranslator"]
```

- [ ] **Step 2: 写最小 translator 实现**

```python
# backend/agent_framework/external/langgraph_translators.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence


@dataclass(frozen=True)
class LangGraphRequestTranslator:
    adapter_id: str
    framework_name: str
    assistant_id: str
    endpoint: str

    def translate(
        self,
        *,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "adapter_id": str(self.adapter_id or "").strip(),
            "framework_name": str(self.framework_name or "").strip(),
            "run_id": str(run_id or "").strip(),
            "assistant_id": str(self.assistant_id or "").strip(),
            "endpoint": str(self.endpoint or "").strip(),
            "messages": [self._normalize_message(message) for message in messages or []],
            "execution_context": self._normalize_execution_context(execution_context or {}),
        }

    @staticmethod
    def _normalize_message(message: Mapping[str, Any]) -> Dict[str, str]:
        role = str((message or {}).get("role") or "user").strip().lower() or "user"
        content = str((message or {}).get("content") or "").strip()
        return {
            "role": role,
            "content": content,
        }

    @staticmethod
    def _normalize_execution_context(execution_context: Mapping[str, Any]) -> Dict[str, Any]:
        allowed_keys = ("plan_id", "plan_item_id", "run_kind", "scheduler_run_id", "child_run_id")
        return {
            key: execution_context.get(key)
            for key in allowed_keys
            if execution_context.get(key) not in (None, "")
        }
```

- [ ] **Step 3: 运行 translator 单测，确认通过**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator -v
```

Expected:

```text
Ran 2 tests ... OK
```

- [ ] **Step 4: 做一次最小重构，补断言保证空 execution context 不泄漏字段**

在 `tests/agent_framework/test_langgraph_request_translator.py` 追加断言：

```python
        self.assertEqual(payload["execution_context"], {})
```

然后再次运行：

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator -v
```

Expected:

```text
Ran 2 tests ... OK
```

- [ ] **Step 5: 提交 translator 骨架**

```bash
git add backend/agent_framework/external/__init__.py backend/agent_framework/external/langgraph_translators.py tests/agent_framework/test_langgraph_request_translator.py
git commit -m "feat: add langgraph request translator skeleton"
```

---

### Task 3: 文档与后续衔接

**Files:**
- Modify: `docs/change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md`

- [ ] **Step 1: 在设计稿里把 Slice 1 标记为可执行起点**

加入一句明确状态说明：

```md
- Slice 1 是 D-8 的推荐第一落点，落成后不应修改任何 route、health 或前端行为。
```

- [ ] **Step 2: 自查计划与设计稿是否一致**

检查点：

- translator 文件路径是否一致
- `run_id / messages / execution_context` 是否仍是唯一输入
- 是否未引入网络或 route 改动

Expected:

```text
无额外差异；计划与设计稿保持一致
```

- [ ] **Step 3: 提交文档衔接说明**

```bash
git add docs/change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md
git commit -m "docs: mark slice 1 as d8 execution entrypoint"
```

---

## 自检结果

- Spec coverage：
  - D-8 Slice 1 的 translator 骨架、测试、文件落点、回滚友好性都已有对应任务。
- Placeholder scan：
  - 本计划未使用 `TODO / TBD / implement later / similar to task N` 这类占位表达。
- Type consistency：
  - 统一使用 `LangGraphRequestTranslator.translate(...)`
  - 统一使用 `execution_context` 白名单字段：
    - `plan_id`
    - `plan_item_id`
    - `run_kind`
    - `scheduler_run_id`
    - `child_run_id`

