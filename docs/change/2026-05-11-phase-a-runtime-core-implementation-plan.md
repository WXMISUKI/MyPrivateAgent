# Phase A Runtime Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `MyPrivateAgent` 当前分散在 `runtime / scheduler / trace / policy / governance UI` 的执行与治理对象收口成统一的 Phase A 运行时内核主线。

**Architecture:** 采用兼容演进路线，不推倒现有 `ChatService / SchedulerService / GovernanceTimelinePanel`，而是在现有骨架中插入正式的运行时对象、审批对象和 run-scoped trace 入口。后端先统一协议和查询来源，前端只做最小 DTO 对齐，不抢先做平台化大改版。

**Tech Stack:** Python 3、FastAPI、SQLAlchemy、Vue 3、Vitest、unittest

---

## 实施状态（2026-05-11）

Phase A 第一轮已经按本计划完成，采用子智能体实现、规格复核、质量复核的节奏推进。与计划相比，本轮保持兼容演进，没有推倒既有 `ChatService / SchedulerService / GovernanceTimelinePanel` 主链路。

### 已完成

- Task 1：统一运行时对象与事件协议。`runtime.py / events.py` 已补齐 runtime core 快照、事件 envelope 兼容字段和对应回归测试。
- Task 2：引入正式审批对象并升级策略结果。新增 `approval_engine_service.py`，策略结果区分阻断和需审批，审批状态对象已进入 runtime entities。
- Task 3：将 scheduler 与 run trace 收口到 run-scoped 主线。显式 `run_id / child_run_id / plan_id / item_id` 优先级已固化，scheduler 序列化已补齐 child run 与 approval request 字段。
- Task 4：更新 chat runtime 映射与后端治理 DTO。审批事件映射为统一 governance trace，runtime surface schema 已结构化。
- Task 5：前端治理台最小 Phase A 对齐。`GovernanceTimelinePanel` 展示当前 run 和待处理审批，`RuntimeSurfacePanel` 展示 runtime core 与 governance overview contract。
- Task 6：Phase A 回归与文档收口。后端与前端局部回归已通过，本文档与总蓝图已同步状态。
- Final review 修复：高风险工具的 `requires_approval` 已从 policy/hook 贯通到 harness，并由 `RuntimeSurfaceService` 正式下发 `runtime_core / governance_overview` 合同，避免前端只显示占位。`waiting_approval` 也已向 `AgentHarness -> Orchestrator -> ChatService / Router / Scheduler` 真实链路传播，避免审批暂停被误处理为计划或 child run 完成。

### 验证记录

```powershell
python -m unittest tests.agent_framework.test_events tests.agent_framework.test_policy_engine_service tests.agent_framework.test_agent_hook_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_approval_engine_service tests.agent_framework.test_orchestrator_service -v
```

结果：`Ran 90 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`2 passed, 33 passed`

### 残余风险

- `ArtifactRef` 仍主要作为设计对象保留，尚未形成独立 registry。
- `Adapter Health` 仍未作为正式 runtime surface contract 落地，建议在 Phase B adapter 契约中补齐。
- 高风险工具识别仍是关键字策略，但现在已贯通到审批等待事件；后续需要升级为组织/项目/角色可配置策略。
- 部分旧 planner item metadata 仍作为兼容层存在，后续应继续迁移到正式 run / child-run 真相源。

---

## 文件结构与职责

### 后端核心

- 修改: `backend/agent_framework/runtime.py`
  - 收口 `AgentState`、`AgentRunKind`、`AgentRunContext`
  - 增加 stop reason / error category / approval state 的统一快照输出
- 修改: `backend/agent_framework/events.py`
  - 扩展 `AgentEvent` 为统一运行时事件协议壳
  - 补齐 source / severity / summary / detail / payload 的兼容构造能力
- 新增: `backend/services/approval_engine_service.py`
  - 提供正式的 `ApprovalRequest` 构造、更新和序列化入口
- 修改: `backend/services/policy_engine_service.py`
  - 将“阻断结果”与“需要审批”区分开
  - 输出结构升级为可承接审批对象的策略结果
- 修改: `backend/services/scheduler_runtime_entities.py`
  - 对齐 `scheduler_run / child_run / approval_request` 的统一字段
- 修改: `backend/services/scheduler_service.py`
  - 让 scheduler 正式写入 `run_id / child_run_id / approval_request`
  - 将 child run / approval request 当成运行时对象而不是附属 metadata
- 修改: `backend/services/run_trace_service.py`
  - 增加 run-scoped 查询优先级
  - 降低对“最新 active planner item”的隐式依赖
- 修改: `backend/services/chat_service.py`
  - 将 runtime event 到 governance trace 的映射对齐新协议
- 修改: `backend/services/orchestrator_service.py`
  - `done` 载荷保留 `state / stop_reason / approval_request_id` 等运行时治理字段
- 修改: `backend/orchestrator.py`
  - 透传 `status / state` 等非终止 runtime 事件，等待审批时不误触发子智能体 collect / merge
- 修改: `backend/schemas_runtime_surface.py`
  - 对外暴露最小 `run / approval / audit / adapter_health` DTO

### 前端最小对齐

- 修改: `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - 能显示 `run_id / child_run_id / approval status`
- 修改: `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - 能显示新的 runtime core contract 和 approval contract

### 测试

- 修改: `tests/agent_framework/test_events.py`
- 修改: `tests/agent_framework/test_policy_engine_service.py`
- 修改: `tests/agent_framework/test_run_trace_service.py`
- 修改: `tests/agent_framework/test_scheduler_service.py`
- 修改: `tests/agent_framework/test_chat_service.py`
- 修改: `tests/agent_framework/test_orchestrator_service.py`
- 新增: `tests/agent_framework/test_approval_engine_service.py`
- 修改: `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- 修改: `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`

## Task 1: 统一运行时对象与事件协议

**Files:**
- Modify: `backend/agent_framework/runtime.py`
- Modify: `backend/agent_framework/events.py`
- Test: `tests/agent_framework/test_events.py`

- [ ] **Step 1: 先写运行时对象测试，锁定新快照字段**

```python
class AgentRuntimeTests(unittest.TestCase):
    def test_run_context_snapshot_exposes_runtime_core_fields(self):
        context = AgentRunContext(
            conversation_id=7,
            user_id=9,
            model_name="doubao",
            parent_run_id="run_parent_1",
            run_kind=AgentRunKind.CHAT,
        )
        context.begin_iteration()
        context.transition_to(AgentState.WAITING_APPROVAL, stop_reason="approval_required")
        context.metadata["error_category"] = "tool_governance"
        context.metadata["approval_request_id"] = "apr_001"

        snapshot = context.snapshot()

        self.assertEqual(snapshot["run_id"][:4], "run_")
        self.assertEqual(snapshot["parent_run_id"], "run_parent_1")
        self.assertEqual(snapshot["state"], "waiting_approval")
        self.assertEqual(snapshot["stop_reason"], "approval_required")
        self.assertEqual(snapshot["metadata"]["error_category"], "tool_governance")
        self.assertEqual(snapshot["metadata"]["approval_request_id"], "apr_001")
```

- [ ] **Step 2: 运行后端单测，确认当前实现先失败**

Run: `python -m unittest tests.agent_framework.test_events -v`

Expected: `FAIL`，提示快照里缺少新增字段或断言不匹配。

- [ ] **Step 3: 在 `runtime.py` 最小扩展运行时快照与统一字段**

```python
@dataclass
class AgentRunContext:
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    model_name: str = "unknown"
    run_id: str = field(default_factory=lambda: f"run_{uuid4().hex}")
    parent_run_id: Optional[str] = None
    run_kind: AgentRunKind = AgentRunKind.CHAT
    state: AgentState = AgentState.INIT
    iteration: int = 0
    stop_reason: Optional[str] = None
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    last_state_transition: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_runtime_marker(self, *, error_category: Optional[str] = None, approval_request_id: Optional[str] = None) -> None:
        if error_category:
            self.metadata["error_category"] = error_category
        if approval_request_id:
            self.metadata["approval_request_id"] = approval_request_id

    def snapshot(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "run_kind": self.run_kind.value,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "state": self.state.value,
            "iteration": self.iteration,
            "stop_reason": self.stop_reason,
            "tool_history": list(self.tool_history),
            "state_history": list(self.state_history),
            "metadata": dict(self.metadata),
        }
```

- [ ] **Step 4: 扩展 `events.py`，让事件能够承接 source/severity/summary/detail**

```python
@dataclass(frozen=True)
class AgentEvent:
    type: str
    run_id: str
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex}")
    parent_run_id: Optional[str] = None
    conversation_id: Optional[int] = None
    iteration: Optional[int] = None
    source: Optional[str] = None
    severity: Optional[str] = None
    summary: str = ""
    detail: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": self.type,
            "event_id": self.event_id,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "conversation_id": self.conversation_id,
            "iteration": self.iteration,
            "source": self.source,
            "severity": self.severity,
            "summary": self.summary,
            "detail": self.detail,
            "payload": dict(self.payload),
        }
        for key, value in self.payload.items():
            if key not in data:
                data[key] = value
        return data
```

- [ ] **Step 5: 补充事件工厂测试，验证兼容序列化**

```python
def test_event_factory_supports_runtime_core_metadata(self):
    factory = AgentEventFactory("run_123", conversation_id=42, parent_run_id="run_parent")
    event = factory.build(
        AgentEventType.STATUS,
        {"status_kind": "approval_created", "approval_request_id": "apr_001"},
        iteration=2,
    )
    enriched = AgentEvent(
        type=event.type,
        run_id=event.run_id,
        parent_run_id=event.parent_run_id,
        conversation_id=event.conversation_id,
        iteration=event.iteration,
        source="governance",
        severity="warning",
        summary="审批请求已创建",
        detail="等待人工确认",
        payload=event.payload,
    )
    data = enriched.to_dict()
    self.assertEqual(data["source"], "governance")
    self.assertEqual(data["severity"], "warning")
    self.assertEqual(data["approval_request_id"], "apr_001")
```

- [ ] **Step 6: 重新运行测试并提交**

Run: `python -m unittest tests.agent_framework.test_events -v`

Expected: `OK`

```bash
git add backend/agent_framework/runtime.py backend/agent_framework/events.py tests/agent_framework/test_events.py
git commit -m "feat: normalize runtime core event envelope"
```

## Task 2: 引入正式审批对象并升级策略结果

**Files:**
- Create: `backend/services/approval_engine_service.py`
- Modify: `backend/services/policy_engine_service.py`
- Modify: `backend/services/scheduler_runtime_entities.py`
- Test: `tests/agent_framework/test_approval_engine_service.py`
- Test: `tests/agent_framework/test_policy_engine_service.py`

- [ ] **Step 1: 先写审批服务测试，锁定对象结构**

```python
class ApprovalEngineServiceTests(unittest.TestCase):
    def test_create_tool_approval_request(self):
        service = ApprovalEngineService()
        request = service.create_request(
            run_id="run_123",
            parent_run_id="run_parent",
            target_type="tool",
            target_name="filesystem_write",
            reason_code="high_risk_tool_block",
            tool_args={"path": "/tmp/demo.txt"},
            context={"conversation_id": 99, "user_id": 1, "permission_level": "high"},
        )

        self.assertEqual(request["run_id"], "run_123")
        self.assertEqual(request["target_type"], "tool")
        self.assertEqual(request["status"], "pending")
        self.assertEqual(request["reason_code"], "high_risk_tool_block")
```

- [ ] **Step 2: 运行测试，确认新服务尚不存在**

Run: `python -m unittest tests.agent_framework.test_approval_engine_service -v`

Expected: `ERROR`，提示 `ApprovalEngineService` 未定义。

- [ ] **Step 3: 创建最小审批服务**

```python
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ApprovalRequestRecord:
    approval_request_id: str
    run_id: str
    parent_run_id: str | None
    target_type: str
    target_name: str
    status: str
    reason_code: str
    tool_args: dict
    context: dict
    requested_at: str


class ApprovalEngineService:
    def create_request(self, **kwargs) -> dict:
        record = ApprovalRequestRecord(
            approval_request_id=f"apr_{uuid4().hex}",
            run_id=str(kwargs["run_id"]),
            parent_run_id=kwargs.get("parent_run_id"),
            target_type=str(kwargs["target_type"]),
            target_name=str(kwargs["target_name"]),
            status="pending",
            reason_code=str(kwargs["reason_code"]),
            tool_args=dict(kwargs.get("tool_args") or {}),
            context=dict(kwargs.get("context") or {}),
            requested_at=datetime.now(timezone.utc).isoformat(),
        )
        return asdict(record)
```

- [ ] **Step 4: 将 `PolicyDecision` 从二值阻断升级为“允许 / 拒绝 / 需审批”**

```python
@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool = False
    reason: str = ""
    reason_code: str = ""
    metadata: Optional[Dict[str, Any]] = None


if any(keyword in normalized_tool for keyword in self.high_risk_tool_keywords):
    return PolicyDecision(
        allowed=False,
        requires_approval=True,
        reason="命中高风险工具治理策略，需要进入审批流程。",
        reason_code="high_risk_tool_block",
        metadata={
            "policy": "high_risk_tool_block",
            "tool_name": tool_name,
            "agent_role": subagent_role or None,
        },
    )
```

- [ ] **Step 5: 调整 scheduler runtime entities，让审批对象成为正式状态项**

```python
@dataclass
class ApprovalRequestState:
    approval_request_id: Optional[str] = None
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    child_run_id: Optional[str] = None
    target_type: Optional[str] = None
    target_name: Optional[str] = None
    permission_level: Optional[str] = None
    status: str = "pending"
    reason_code: Optional[str] = None
    requested_at: Optional[str] = None
    completed_at: Optional[str] = None
    tool_args: dict = field(default_factory=dict)
    request_metadata: dict = field(default_factory=dict)
```

- [ ] **Step 6: 补策略测试并提交**

```python
def test_high_risk_tool_requires_approval(self):
    decision = get_policy_engine_service().evaluate_tool_use(
        tool_name="filesystem_write",
        tool_args={"path": "/tmp/demo.txt"},
        context={"agent_role": "planner"},
    )
    self.assertFalse(decision.allowed)
    self.assertTrue(decision.requires_approval)
    self.assertEqual(decision.reason_code, "high_risk_tool_block")
```

Run: `python -m unittest tests.agent_framework.test_approval_engine_service tests.agent_framework.test_policy_engine_service -v`

Expected: `OK`

```bash
git add backend/services/approval_engine_service.py backend/services/policy_engine_service.py backend/services/scheduler_runtime_entities.py tests/agent_framework/test_approval_engine_service.py tests/agent_framework/test_policy_engine_service.py
git commit -m "feat: add approval request runtime contract"
```

## Task 3: 将 scheduler 与 run trace 收口到 run-scoped 主线

**Files:**
- Modify: `backend/services/scheduler_service.py`
- Modify: `backend/services/run_trace_service.py`
- Test: `tests/agent_framework/test_scheduler_service.py`
- Test: `tests/agent_framework/test_run_trace_service.py`

- [ ] **Step 1: 先写 run trace 测试，锁定 run-scoped 优先级**

```python
def test_append_runtime_trace_prefers_explicit_run_scope(self):
    service = RunTraceService(db=object())
    success = service.append_runtime_trace(
        user_id=1,
        conversation_id=99,
        run_id="sched-p10-i24",
        source="scheduler",
        event_type="scheduler_merge_completed",
        summary="调度器已完成汇总",
        payload={"child_count": 3},
    )
    self.assertTrue(success)
    self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["run_id"], "sched-p10-i24")
```

- [ ] **Step 2: 运行测试，确认当前行为还依赖 planner item 推断**

Run: `python -m unittest tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service -v`

Expected: 至少一项 `FAIL`，表现为缺少显式 `approval_request_id`、`child_run_id` 或 run-scoped 优先级不稳定。

- [ ] **Step 3: 在 `scheduler_service.py` 统一写入 child run 与 approval request**

```python
child = {
    "child_execution_id": child_execution_id,
    "child_run_id": child_execution_id,
    "parent_run_id": scheduler_run_id,
    "run_id": child_execution_id,
    "run_kind": "child",
    "agent_role": role,
    "status": status,
}

approval_request = {
    "approval_request_id": approval["approval_request_id"],
    "run_id": scheduler_run_id,
    "parent_run_id": plan_run_id,
    "child_run_id": child_execution_id,
    "target_type": "tool",
    "target_name": tool_name,
    "status": "pending",
    "reason_code": approval["reason_code"],
}
```

- [ ] **Step 4: 在 `run_trace_service.py` 保留兼容逻辑，但显式优先 `run_id / child_run_id`**

```python
target = self._resolve_plan_item_target(
    user_id=user_id,
    conversation_id=conversation_id,
    plan_id=plan_id,
    item_id=item_id,
    run_id=run_id,
    child_run_id=child_run_id,
    prefer_active_when_unspecified=not bool(run_id or child_run_id or item_id),
)
```

- [ ] **Step 5: 补 scheduler 测试，验证审批对象进入 runtime state**

```python
def test_prepare_execution_preserves_runtime_child_and_approval_containers(self):
    state = self.service.prepare_execution(plan=self.plan, item=self.item)
    self.assertIn("execution_context", state)
    self.assertEqual(state["execution_context"]["run_kind"], "scheduler")
    self.assertIsInstance(self.item.item_metadata["child_execution_group"]["children"], list)
    self.assertIn("approval_requests", self.item.item_metadata["child_execution_group"])
```

- [ ] **Step 6: 运行测试并提交**

Run: `python -m unittest tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service -v`

Expected: `OK`

```bash
git add backend/services/scheduler_service.py backend/services/run_trace_service.py tests/agent_framework/test_scheduler_service.py tests/agent_framework/test_run_trace_service.py
git commit -m "refactor: align scheduler and trace with run scoped runtime"
```

## Task 4: 更新 chat runtime 映射与后端治理 DTO

**Files:**
- Modify: `backend/services/chat_service.py`
- Modify: `backend/schemas_runtime_surface.py`
- Test: `tests/agent_framework/test_chat_service.py`

- [ ] **Step 1: 先写 chat runtime trace 测试，锁定审批与 child run 映射**

```python
def test_build_run_trace_maps_approval_runtime_event(self):
    event = {
        "type": "status",
        "run_id": "run_123",
        "payload": {
            "status_kind": "approval_created",
            "approval_request_id": "apr_001",
            "target_type": "tool",
            "target_name": "filesystem_write",
        },
    }
    trace = _build_run_trace_from_runtime_event(event)
    self.assertEqual(trace["source"], "governance")
    self.assertEqual(trace["event_type"], "tool_permission_required")
    self.assertEqual(trace["payload"]["approval_request_id"], "apr_001")
```

- [ ] **Step 2: 运行相关测试，确认新事件类型尚未映射**

Run: `python -m unittest tests.agent_framework.test_chat_service -v`

Expected: `FAIL`，表现为 `trace is None` 或字段缺失。

- [ ] **Step 3: 在 `chat_service.py` 增加审批 / child runtime 事件映射**

```python
if event_type == "status":
    status_kind = str(extract_event_field(event, "status_kind", "") or "").strip()
    if status_kind == "approval_created":
        return {
            "source": "governance",
            "event_type": "tool_permission_required",
            "summary": "运行时已创建审批请求",
            "detail": f"target={extract_event_field(event, 'target_name', '')}",
            "severity": "warning",
            "payload": {
                "approval_request_id": extract_event_field(event, "approval_request_id", ""),
                "target_type": extract_event_field(event, "target_type", ""),
                "target_name": extract_event_field(event, "target_name", ""),
            },
        }
```

- [ ] **Step 4: 在 `schemas_runtime_surface.py` 增加最小 DTO**

```python
runtime_governance_surface = {
    "run_overview": {
        "run_id": "",
        "state": "",
        "run_kind": "",
        "child_run_count": 0,
    },
    "approval_overview": {
        "pending_count": 0,
        "latest_request_id": "",
    },
    "audit_overview": {
        "latest_event_type": "",
        "latest_severity": "",
    },
}
```

- [ ] **Step 5: 运行后端测试并提交**

Run: `python -m unittest tests.agent_framework.test_chat_service tests.agent_framework.test_runtime_surface_service -v`

Expected: `OK`

```bash
git add backend/services/chat_service.py backend/schemas_runtime_surface.py tests/agent_framework/test_chat_service.py
git commit -m "feat: expose runtime core governance dto"
```

## Task 5: 前端治理台做最小 Phase A 对齐

**Files:**
- Modify: `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- Modify: `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- Test: `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- Test: `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`

- [ ] **Step 1: 先补前端测试，锁定 run/approval 展示**

```javascript
it('renders approval runtime metadata in governance timeline', async () => {
  render(GovernanceTimelinePanel, {
    props: {
      currentConversationId: 99,
      currentPlan: { objective: '统一运行时', items: [] },
    },
  })
  expect(screen.getByText(/治理时间线/)).toBeInTheDocument()
})
```

- [ ] **Step 2: 运行前端局部测试，确认当前界面还没有新字段**

Run: `cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js src/components/__tests__/RuntimeSurfacePanel.test.js`

Expected: 至少一项 `FAIL`，提示找不到 run/approval 文案或映射字段。

- [ ] **Step 3: 在 `GovernanceTimelinePanel.vue` 增加审批与 run 元信息展示**

```vue
<div class="summary-card">
  <span class="summary-label">当前 Run</span>
  <strong>{{ focusRuntimeRunId || '-' }}</strong>
</div>
<div class="summary-card">
  <span class="summary-label">待处理审批</span>
  <strong>{{ pendingApprovalCount }}</strong>
</div>
```

- [ ] **Step 4: 在 `RuntimeSurfacePanel.vue` 增加 runtime core / approval contract 卡片**

```vue
<div v-if="runtimeCoreContract" class="panel-card">
  <div class="card-head">
    <h3>Runtime Core Contract</h3>
    <span class="muted">统一 run / child-run / approval / artifact 的最小协议面</span>
  </div>
  <ul>
    <li><code>run_state_model</code>: {{ runtimeCoreContract.run_state_model || '-' }}</li>
    <li><code>approval_model</code>: {{ runtimeCoreContract.approval_model || '-' }}</li>
  </ul>
</div>
```

- [ ] **Step 5: 运行局部前端测试并提交**

Run: `cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js src/components/__tests__/RuntimeSurfacePanel.test.js`

Expected: `PASS`

```bash
git add frontend-vue/src/components/GovernanceTimelinePanel.vue frontend-vue/src/components/RuntimeSurfacePanel.vue frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js
git commit -m "feat: surface phase-a runtime governance fields"
```

## Task 6: Phase A 回归与文档收口

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/change/2026-05-11-enterprise-agent-runtime-blueprint.md`
- Modify: `docs/change/2026-05-11-phase-a-runtime-core-implementation-plan.md`

- [x] **Step 1: 运行 Phase A 相关后端回归**

Run:

```bash
python -m unittest tests.agent_framework.test_events tests.agent_framework.test_policy_engine_service tests.agent_framework.test_agent_hook_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_approval_engine_service tests.agent_framework.test_orchestrator_service -v
```

Expected: `OK`

Actual: `Ran 90 tests ... OK`

- [x] **Step 2: 运行 Phase A 相关前端局部回归**

Run:

```bash
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js src/components/__tests__/RuntimeSurfacePanel.test.js
```

Expected: `PASS`

Actual: `2 passed, 33 passed`

- [x] **Step 3: 更新设计稿中的 Phase A 状态备注**

```md
## Phase A 实施状态

- 运行时对象: 已落地
- 审批对象: 已落地
- run-scoped trace: 已落地
- 前端最小对齐: 已落地
```

- [x] **Step 4: 更新文档索引**

```bash
git add docs/README.md docs/change/2026-05-11-enterprise-agent-runtime-blueprint.md docs/change/2026-05-11-phase-a-runtime-core-implementation-plan.md
git commit -m "docs: add phase-a runtime core implementation plan"
```

Note: 本轮未自动提交，交由最终人工确认后再决定是否提交。

## 自检

### Spec 覆盖

- `run / child-run / approval / artifact` 一等对象：由 Task 1、Task 2、Task 3 覆盖
- `scheduler` 升级为第一类运行时服务：由 Task 3 覆盖
- `run / approval / audit / adapter health` 最小前端对齐：由 Task 4、Task 5 覆盖
- 保持兼容演进，不推倒现有骨架：所有任务都基于现有文件修改而不是大搬迁

### Placeholder 扫描

- 本计划未使用 `TODO / TBD / implement later / similar to task N` 这类占位表达
- 每个任务都给出了明确文件、测试入口和最小代码骨架

### 类型一致性

- 统一使用 `run_id / parent_run_id / child_run_id / approval_request_id`
- 策略结果统一使用 `allowed / requires_approval / reason_code`
- 前端显示统一围绕 `run / approval / audit` 三类核心数据
