# LangGraph External Pilot Route Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `langgraph_draft` 增加受控 `external-pilot` 入口，把 request translator、runtime client、event translator 串成一条最小真实外部执行链，同时保持 trace / audit / snapshot / front-end governance 闭环。

**Architecture:** 这是 D-8 的最后一个执行切片，只新增一个独立 route 和 service 调用路径，不改 `pilot-run` 语义，不碰 chat 主路径。external pilot 只接受 `langgraph_draft`，并且必须同时满足 `configuration_status == ready` 与 `ENABLE_LANGGRAPH_EXTERNAL_PILOT=true`。

**Tech Stack:** Python 3、FastAPI、Pydantic、httpx、unittest、现有 run trace service

---

## 范围边界

本计划只覆盖 D-8 Slice 5：

- 新增 external pilot route
- 串起 request/client/event/output translators
- 写 trace / audit / snapshot
- 增加 service / route / unittest

本计划明确不做：

- 不改 `pilot-run`
- 不改 `precheck`
- 不改前端
- 不接 chat 主路径
- 不做 workflow 编辑

---

## 文件结构与职责

- Modify: `backend/services/framework_adapter_runtime_service.py`
  - 新增 `execute_external_adapter_run(...)`
  - 串接 request translator、runtime client、event translator、output translator
- Modify: `backend/routers/health.py`
  - 新增 `POST /api/runtime-framework-adapters/external-pilot`
- Modify: `backend/schemas_runtime_surface.py`
  - 新增 `FrameworkAdapterExternalPilotRunRequest`
- Modify: `backend/agent_framework/framework_adapters.py`
  - 允许 `LangGraphDraftAdapter` 在 external pilot gate 打开时被执行
- Create: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`
  - 锁定成功路径、关门路径、最小 trace/audit 形状
- Modify: `tests/agent_framework/test_health_router.py`
  - 锁定 route 行为

---

### Task 1: 先锁 service 级测试

**Files:**
- Create: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`

- [ ] **Step 1: 写开关关闭时拒绝执行的测试**

```python
import unittest
from unittest.mock import patch

from backend.agent_framework.framework_adapters import AgentFrameworkAdapterRegistry, LangGraphDraftAdapter
from backend.services.framework_adapter_runtime_service import FrameworkAdapterRuntimeService


class FrameworkAdapterExternalPilotTests(unittest.TestCase):
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_rejects_when_gate_disabled(self, _mock_package_available):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        with self.assertRaises(ValueError) as ctx:
            service.execute_external_adapter_run(
                adapter_id="langgraph_draft",
                run_id="run-1",
                messages=[{"role": "user", "content": "hello"}],
                execution_context={},
            )

        self.assertEqual(str(ctx.exception), "external pilot is not enabled")
```

- [ ] **Step 2: 写成功路径测试，锁定最小串联行为**

```python
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_runs_translators_and_returns_snapshot(self, _mock_package_available):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-2",
            messages=[{"role": "user", "content": "hello"}],
            execution_context={"plan_id": 101},
        )

        self.assertEqual(result["adapter_id"], "langgraph_draft")
        self.assertEqual(result["run_id"], "run-2")
        self.assertIn("snapshot_ref", result)
        self.assertTrue(result["events"])
```

- [ ] **Step 3: 运行测试，确认当前失败**

Run:

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_runtime_service_external_pilot -v
```

Expected:

```text
ERROR: execute_external_adapter_run not defined
```

---

### Task 2: 实现 external pilot service

**Files:**
- Modify: `backend/services/framework_adapter_runtime_service.py`
- Modify: `backend/agent_framework/framework_adapters.py`
- Test: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`

- [ ] **Step 1: 在 service 中新增 `execute_external_adapter_run(...)`**

实现要求：

- 只接受 `langgraph_draft`
- 先读取 adapter.health / can_execute
- 构造 request translator
- 调用 runtime client
- 遍历 streaming chunks 并调用 event translator
- 取 final output 并调用 output translator
- 写 trace / audit / snapshot

最小成功输出包含：

- `adapter_id`
- `run_id`
- `translated_input`
- `events`
- `final_output`
- `snapshot_ref`

- [ ] **Step 2: 在 adapter 层允许 external pilot**

要求：

- `LangGraphDraftAdapter.can_execute()` 仍然由 Slice 4 的 gate 控制
- service 层调用时只要 gate 开启即可执行

- [ ] **Step 3: 运行测试，确认通过**

Run:

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_runtime_service_external_pilot -v
```

Expected:

```text
Ran 2 tests ... OK
```

---

### Task 3: 新增 route 与 schema

**Files:**
- Modify: `backend/schemas_runtime_surface.py`
- Modify: `backend/routers/health.py`
- Modify: `tests/agent_framework/test_health_router.py`

- [ ] **Step 1: 新增 request schema**

```python
class FrameworkAdapterExternalPilotRunRequest(BaseModel):
    adapter_id: str
    run_id: str
    messages: List[FrameworkAdapterPilotMessage]
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    execution_context: Optional[dict] = None
```

- [ ] **Step 2: 新增 route**

```python
@router.post("/runtime-framework-adapters/external-pilot")
def run_framework_adapter_external_pilot(
    request: FrameworkAdapterExternalPilotRunRequest,
    db: Session = Depends(get_db),
):
    if not ENABLE_LANGGRAPH_EXTERNAL_PILOT:
        raise HTTPException(status_code=409, detail="framework adapter external pilot is disabled; set ENABLE_LANGGRAPH_EXTERNAL_PILOT=true to enable it")
    try:
        return get_framework_adapter_runtime_service().execute_external_adapter_run(
            adapter_id=request.adapter_id,
            run_id=request.run_id,
            messages=[item.model_dump() for item in request.messages],
            execution_context=request.execution_context or {},
            db=db,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

- [ ] **Step 3: 补 route 测试**

```python
    def test_external_pilot_route_rejects_when_disabled(self):
        ...
```

```python
    def test_external_pilot_route_accepts_when_enabled(self):
        ...
```

- [ ] **Step 4: 运行 route 测试**

Run:

```powershell
python -m unittest tests.agent_framework.test_health_router -v
```

Expected:

```text
新增的 external pilot route 测试通过
```

---

### Task 4: 文档衔接

**Files:**
- Modify: `docs/change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md`

- [ ] **Step 1: 在 D-8 设计稿里补 Slice 5 约束**

```md
- Slice 5 只新增独立 external-pilot route，不改 `pilot-run` 语义，也不接 chat 主路径。
```

- [ ] **Step 2: 合并验证**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator tests.agent_framework.test_langgraph_runtime_client tests.agent_framework.test_langgraph_event_translator tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_framework_adapter_runtime_service_external_pilot tests.agent_framework.test_health_router -v
```

Expected:

```text
全部通过
```

---

## 自检结果

- Spec coverage：
  - external pilot route、service、schema、测试、文档衔接都有任务。
- Placeholder scan：
  - 本计划未使用 `TODO / TBD / implement later / similar to task N` 这类占位表达。
- Type consistency：
  - 统一 route 名：`/runtime-framework-adapters/external-pilot`
  - 统一开关名：`ENABLE_LANGGRAPH_EXTERNAL_PILOT`
  - 统一 service 名：`execute_external_adapter_run(...)`

