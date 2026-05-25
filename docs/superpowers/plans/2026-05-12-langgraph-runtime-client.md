# LangGraph Runtime Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `langgraph_draft` 增加可注入 transport 的最小 `LangGraphRuntimeClient`，在不发真实网络请求的前提下固定 `invoke / stream` 接口、超时参数和平台错误分类。

**Architecture:** 继续采用 D-8 小切片策略，只落 client 模块与对应单测，不接 route、不接 service、不改 `FrameworkAdapterRuntimeService`。client 只负责对 transport 的调用和错误包装，不负责 request 翻译、事件翻译或 trace/audit。

**Tech Stack:** Python 3、httpx（错误类型对齐）、unittest、可注入 stub transport

---

## 范围边界

本计划只覆盖 D-8 Slice 2：

- 新建 `LangGraphRuntimeClient`
- 新建最小错误类型
- 新建 `invoke / stream` 单测

本计划明确不做：

- 不发真实 HTTP 请求
- 不修改 `LangGraphDraftAdapter`
- 不接入 `FrameworkAdapterRuntimeService`
- 不新增任何 API route
- 不修改前端

---

## 文件结构与职责

- Create: `backend/agent_framework/external/langgraph_client.py`
  - 定义 `LangGraphRuntimeClient`
  - 定义平台侧最小外部 runtime 错误包装
- Modify: `backend/agent_framework/external/__init__.py`
  - 导出 `LangGraphRuntimeClient` 与错误类型
- Create: `tests/agent_framework/test_langgraph_runtime_client.py`
  - 锁定 `invoke / stream` 成功路径
  - 锁定错误分类：
    - `connectivity_error`
    - `authentication_error`
    - `protocol_error`
    - `upstream_runtime_error`

---

### Task 1: 先锁 client contract 测试

**Files:**
- Create: `tests/agent_framework/test_langgraph_runtime_client.py`

- [ ] **Step 1: 写成功路径测试，锁定 `invoke()` 接口**

```python
import unittest

from backend.agent_framework.external.langgraph_client import LangGraphRuntimeClient


class _StubTransport:
    def __init__(self):
        self.calls = []

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        self.calls.append(
            {
                "endpoint": endpoint,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
                "headers": headers,
            }
        )
        return {"status": "accepted", "output": {"content": "ok"}}


class LangGraphRuntimeClientTests(unittest.TestCase):
    def test_invoke_delegates_to_transport_and_returns_payload(self):
        transport = _StubTransport()
        client = LangGraphRuntimeClient(transport=transport, timeout_seconds=9.5)

        result = client.invoke(
            endpoint="http://localhost:8123/langgraph",
            payload={"run_id": "run_1"},
            headers={"Authorization": "Bearer demo"},
        )

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(transport.calls[0]["endpoint"], "http://localhost:8123/langgraph")
        self.assertEqual(transport.calls[0]["payload"], {"run_id": "run_1"})
        self.assertEqual(transport.calls[0]["timeout_seconds"], 9.5)
        self.assertEqual(transport.calls[0]["headers"]["Authorization"], "Bearer demo")
```

- [ ] **Step 2: 写成功路径测试，锁定 `stream()` 接口**

```python
class _StubStreamingTransport:
    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        yield {"type": "status", "message": "accepted"}
        yield {"type": "output", "content": "hello"}

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("invoke should not be called in stream test")


    def test_stream_yields_transport_chunks(self):
        client = LangGraphRuntimeClient(
            transport=_StubStreamingTransport(),
            timeout_seconds=4.0,
        )

        chunks = list(
            client.stream(
                endpoint="http://localhost:8123/langgraph",
                payload={"run_id": "run_2"},
                headers={},
            )
        )

        self.assertEqual(
            chunks,
            [
                {"type": "status", "message": "accepted"},
                {"type": "output", "content": "hello"},
            ],
        )
```

- [ ] **Step 3: 写失败测试，锁定错误分类**

```python
import httpx

from backend.agent_framework.external.langgraph_client import LangGraphRuntimeClientError


class _StubErrorTransport:
    def __init__(self, exc):
        self.exc = exc

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise self.exc

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise self.exc


    def test_invoke_wraps_connectivity_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(httpx.ConnectError("connect failed")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "connectivity_error")
```

- [ ] **Step 4: 再补三类错误测试**

```python
    def test_invoke_wraps_authentication_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(PermissionError("401 unauthorized")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "authentication_error")

    def test_invoke_wraps_protocol_error_when_transport_returns_non_mapping(self):
        class _BadTransport:
            def invoke(self, *, endpoint, payload, timeout_seconds, headers):
                return "not-a-dict"

            def stream(self, *, endpoint, payload, timeout_seconds, headers):
                return iter(())

        client = LangGraphRuntimeClient(transport=_BadTransport())

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "protocol_error")

    def test_invoke_wraps_unknown_errors_as_upstream_runtime_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(RuntimeError("upstream exploded")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "upstream_runtime_error")
```

- [ ] **Step 5: 运行测试，确认当前失败**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_runtime_client -v
```

Expected:

```text
ERROR: No module named 'backend.agent_framework.external.langgraph_client'
```

---

### Task 2: 实现最小 runtime client

**Files:**
- Create: `backend/agent_framework/external/langgraph_client.py`
- Modify: `backend/agent_framework/external/__init__.py`
- Test: `tests/agent_framework/test_langgraph_runtime_client.py`

- [ ] **Step 1: 新建 client 错误类型与默认 transport 协议**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Mapping, Protocol


@dataclass
class LangGraphRuntimeClientError(RuntimeError):
    error_type: str
    detail: str

    def __str__(self) -> str:
        return f"{self.error_type}: {self.detail}"


class LangGraphTransport(Protocol):
    def invoke(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        timeout_seconds: float,
        headers: Mapping[str, str],
    ) -> Mapping[str, Any]:
        ...

    def stream(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        timeout_seconds: float,
        headers: Mapping[str, str],
    ) -> Iterator[Mapping[str, Any]]:
        ...
```

- [ ] **Step 2: 写最小 client 实现**

```python
import httpx


class LangGraphRuntimeClient:
    def __init__(self, *, transport: LangGraphTransport, timeout_seconds: float = 10.0):
        self.transport = transport
        self.timeout_seconds = float(timeout_seconds)

    def invoke(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        try:
            result = self.transport.invoke(
                endpoint=endpoint,
                payload=payload,
                timeout_seconds=self.timeout_seconds,
                headers=dict(headers or {}),
            )
        except Exception as exc:
            raise self._wrap_error(exc) from exc
        if not isinstance(result, Mapping):
            raise LangGraphRuntimeClientError(
                error_type="protocol_error",
                detail="transport invoke returned a non-mapping payload",
            )
        return result

    def stream(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
    ) -> Iterator[Mapping[str, Any]]:
        try:
            iterator = self.transport.stream(
                endpoint=endpoint,
                payload=payload,
                timeout_seconds=self.timeout_seconds,
                headers=dict(headers or {}),
            )
            for item in iterator:
                if not isinstance(item, Mapping):
                    raise LangGraphRuntimeClientError(
                        error_type="protocol_error",
                        detail="transport stream yielded a non-mapping chunk",
                    )
                yield item
        except LangGraphRuntimeClientError:
            raise
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    @staticmethod
    def _wrap_error(exc: Exception) -> LangGraphRuntimeClientError:
        if isinstance(exc, httpx.ConnectError | httpx.TimeoutException):
            return LangGraphRuntimeClientError("connectivity_error", str(exc))
        if isinstance(exc, PermissionError):
            return LangGraphRuntimeClientError("authentication_error", str(exc))
        return LangGraphRuntimeClientError("upstream_runtime_error", str(exc))
```

- [ ] **Step 3: 导出 client 与错误类型**

```python
# backend/agent_framework/external/__init__.py

from .langgraph_client import LangGraphRuntimeClient, LangGraphRuntimeClientError
from .langgraph_translators import LangGraphRequestTranslator

__all__ = [
    "LangGraphRequestTranslator",
    "LangGraphRuntimeClient",
    "LangGraphRuntimeClientError",
]
```

- [ ] **Step 4: 运行单测，确认全部通过**

Run:

```powershell
python -m unittest tests.agent_framework.test_langgraph_runtime_client -v
```

Expected:

```text
Ran 6 tests ... OK
```

---

### Task 3: 文档衔接与最小风险说明

**Files:**
- Modify: `docs/change/2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md`

- [ ] **Step 1: 在 D-8 设计稿里补一条 Slice 2 约束**

```md
- Slice 2 的 runtime client 只负责 transport 调用和错误包装，不负责 request shape、event mapping 或 trace 写入。
```

- [ ] **Step 2: 自查计划与设计稿一致性**

检查点：

- 是否仍然不触碰 route/service/front-end
- 是否只有 client 与错误分类
- 是否 transport 可注入、无需真实网络

Expected:

```text
一致，无额外范围漂移
```

---

## 自检结果

- Spec coverage：
  - D-8 Slice 2 的 client 骨架、错误分类、测试、文档衔接都已有任务。
- Placeholder scan：
  - 本计划未使用 `TODO / TBD / implement later / similar to task N` 这类占位表达。
- Type consistency：
  - 统一使用 `LangGraphRuntimeClient.invoke(...)`
  - 统一使用 `LangGraphRuntimeClient.stream(...)`
  - 统一错误类型 `LangGraphRuntimeClientError`
  - 统一错误分类：
    - `connectivity_error`
    - `authentication_error`
    - `protocol_error`
    - `upstream_runtime_error`

