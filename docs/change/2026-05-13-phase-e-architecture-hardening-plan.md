# Phase E Architecture Hardening And Productization Cleanup

> 目标读者：继续维护 `MyPrivateAgent` 通用智能体底座的开发者、评审者、后续垂域智能体接入方。

## 1. 阶段定位

Phase A ~ D 已经完成通用智能体底座的第一轮收口：

- Runtime Core 已具备 run / child run / event / approval / trace / audit 的基本一等对象边界
- Capability Layer 已具备工具、MCP、skill、memory、command、framework adapter 的统一接入雏形
- Governance Layer 已具备 doctor / health / runtime surface / governance timeline 的诊断闭环
- Framework Adapter 已具备 readiness、precheck、external pilot、错误分布和前端过滤闭环

Phase E 不再优先新增能力，而是做架构硬化和产品化整理。目标是让当前底座在接入反诈、评估、助手等垂域智能体前，先把内部 seam 变深、目录更清晰、文档从“阶段日志”升级为“当前事实入口”。

## 2. 设计原则

1. 不推倒重写。
2. 优先抽重复逻辑和过胖模块，不改变对外 contract。
3. 保留兼容入口，逐步迁移调用方。
4. 每一刀都配最小回归验证。
5. 文档记录“当前事实”和“下一步边界”，避免继续扩成长篇历史说明。

## 3. 当前完成：Framework Adapter Diagnostics Seam

### 背景问题

`external_pilot_failure_counts` 和 `latest_external_pilot_failure` 原先分别在：

- `backend/routers/health.py`
- `backend/scripts/doctor.py`

中各自实现了一遍。虽然行为一致，但这会带来三个长期问题：

- 统计窗口、样本数、错误类型聚合规则容易漂移
- doctor CLI 与 health API 的治理语义可能不一致
- 后续要把诊断结果接入 Runtime Surface、CI gate 或 adapter dashboard 时，会继续复制逻辑

### 本次调整

新增：

- `backend/services/framework_adapter_diagnostics_service.py`

提供统一 seam：

- `FrameworkAdapterDiagnosticsService.collect_latest_external_error_summary(...)`
- `FrameworkAdapterDiagnosticsService.collect_external_error_counts(...)`
- `get_framework_adapter_diagnostics_service()`

保留兼容入口：

- `backend/routers/health.py::_collect_latest_framework_adapter_external_error_summary`
- `backend/routers/health.py::_collect_framework_adapter_external_error_counts`
- `backend/scripts/doctor.py::_collect_latest_framework_adapter_external_error_summary`
- `backend/scripts/doctor.py::_collect_framework_adapter_external_error_counts`

这些入口现在只做薄封装，实际规则统一下沉到 diagnostics service。

### 保持不变的 Contract

`external_pilot_failure_counts` 仍保持：

```json
{
  "total": 3,
  "window_scope": "recent_plan_items",
  "sample_size": 50,
  "by_error_type": {
    "protocol_error": 2,
    "configuration_error": 1
  }
}
```

语义保持不变：

- `window_scope = recent_plan_items`：统计最近 PlanItem 的 trace，不代表全量历史。
- `sample_size = 50`：默认最多抽取最近 50 个 PlanItem，并对每个 PlanItem 查询最近 50 条 external error trace。
- `by_error_type`：按 external pilot 错误类型聚合。

## 4. 验证结果

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_doctor_script -v
```

结果：

- `Ran 25 tests`
- `OK`

## 5. 下一步建议

### E-2：拆分 Framework Adapter SPI 文件

建议把 `backend/agent_framework/framework_adapters.py` 拆为：

- `framework_adapter_spi/base.py`
- `framework_adapter_spi/health.py`
- `framework_adapter_spi/registry.py`
- `framework_adapter_spi/noop.py`
- `framework_adapter_spi/local_fake.py`
- `framework_adapter_spi/langgraph_draft.py`

目标是让 adapter SPI 更像独立框架扩展点，而不是一个持续增长的单文件。

### 实施状态（2026-05-13）

已完成。

本次没有把 `backend/agent_framework/framework_adapters.py` 直接改成同名目录，而是保留它作为 public facade，原因是现有后端、测试和后续垂域项目都可能依赖：

```python
from backend.agent_framework.framework_adapters import ...
```

当前实际结构为：

- `backend/agent_framework/framework_adapters.py`：稳定 public facade，负责导出旧 API、读取配置开关、构建默认 registry。
- `backend/agent_framework/framework_adapter_spi/health.py`：`FrameworkAdapterHealth`。
- `backend/agent_framework/framework_adapter_spi/base.py`：`AgentFrameworkAdapter` 抽象 SPI。
- `backend/agent_framework/framework_adapter_spi/noop.py`：占位 adapter。
- `backend/agent_framework/framework_adapter_spi/local_fake.py`：本地 pilot adapter。
- `backend/agent_framework/framework_adapter_spi/registry.py`：adapter registry。
- `backend/agent_framework/framework_adapter_spi/langgraph_draft.py`：LangGraph readiness 与 external pilot gate。

兼容性边界：

- 旧 import 路径保持不变。
- 旧测试中 patch `backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_*` 仍然有效。
- `LangGraphDraftAdapter` 会优先读取 public facade 上的配置值，避免拆分后出现测试、运行时和配置读取漂移。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_runtime_service_external_pilot -v
```

结果：

- `Ran 25 tests`
- `OK`

### E-3：拆分 FrameworkAdapterRuntimeService

建议把 `backend/services/framework_adapter_runtime_service.py` 拆成：

- request / event / output translator orchestration
- precheck service
- pilot execution service
- timeline recording helper
- validation helpers

目标是让 pilot 执行、readiness 预检、trace/audit 记录彼此解耦。

### 实施状态（2026-05-13）

已完成第一轮拆分。

当前结构：

- `backend/services/framework_adapter_runtime_service.py`：保留 public runtime service facade，负责 adapter 查找、执行闸门、结果编排和兼容方法。
- `backend/services/framework_adapter_external_pilot_service.py`：负责 LangGraph external pilot 的 request translation、probe validation、stream/invoke、错误分类和事件翻译。
- `backend/services/framework_adapter_timeline_service.py`：负责 framework adapter pilot / external pilot / precheck 的 trace 与 audit 记录。

关键边界：

- `FrameworkAdapterRuntimeService.execute_adapter_run(...)` 对外行为不变。
- `FrameworkAdapterRuntimeService.execute_external_adapter_run(...)` 对外行为不变。
- `FrameworkAdapterRuntimeService.precheck_adapter(...)` 对外行为不变。
- `get_run_trace_service` 通过延迟 lambda 注入给 timeline recorder，保留现有测试和运行时 patch 能力。
- external pilot 的配置读取仍通过 public facade 上的 `LANGGRAPH_*` 值完成，避免拆分后配置漂移。

文件规模已从单文件集中承担所有职责，拆为三个较小模块：

- `framework_adapter_runtime_service.py`：约 220 行
- `framework_adapter_external_pilot_service.py`：约 250 行
- `framework_adapter_timeline_service.py`：约 220 行

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_doctor_script tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_runtime_service_external_pilot -v
```

结果：

- `Ran 50 tests`
- `OK`

### E-4：前端治理台组件瘦身

`RuntimeSurfacePanel.vue` 与 `GovernanceTimelinePanel.vue` 已经承担了过多职责。建议拆出：

- AdapterHealthCard
- ExternalPilotFailureSummary
- RuntimeContractSnapshot
- GovernanceTimelineFilters
- GovernanceTimelineExternalFailureCard

目标是保持治理台可读、可测试、可继续扩展。

### 实施状态（2026-05-13）

已完成第一轮拆分。

本轮优先拆 `RuntimeSurfacePanel.vue` 中的 external pilot failure summary，因为它同时承担：

- 最近一次 external pilot 失败摘要
- 失败总数 / 窗口 / 样本数展示
- 错误分布格式化
- 错误类型过滤按钮
- 当前路由激活态
- 快照时间线跳转入口

新增：

- `frontend-vue/src/components/AdapterExternalPilotFailureSummary.vue`

父组件保留：

- adapter health contract 归一化
- 当前路由态读取
- 跳转到治理时间线
- 跳转到指定 snapshot

子组件负责：

- failure / counts 展示
- 错误类型标签格式化
- 失败统计格式化
- 错误分布按钮渲染
- active error type 高亮
- 通过 `open-snapshot` / `open-failure-type` 事件通知父组件

兼容性边界：

- UI 文案保持不变。
- `governance_error_type` 路由激活态保持不变。
- 点击错误分布进入 Governance Timeline 的路径保持不变。
- 点击“查看时间线”进入 snapshot 过滤路径保持不变。

当前文件规模：

- `RuntimeSurfacePanel.vue`：约 1958 行
- `AdapterExternalPilotFailureSummary.vue`：约 266 行

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1 passed`
- `22 passed`

### 第二轮拆分（2026-05-13）

已继续拆分 adapter 执行结果区块。

新增：

- `frontend-vue/src/components/AdapterPilotResultCard.vue`

覆盖三类结果：

- `variant = precheck`：展示 adapter precheck 的 readiness、configuration status、execution mode、阻塞原因、修复命令。
- `variant = external`：展示 LangGraph external pilot 的 status、snapshot、错误类型 / 错误详情或最终输出。
- `variant = local`：展示本地 fake adapter pilot 的 run_id、event_count、snapshot 和最终输出。

父组件保留：

- 是否可以运行 precheck / external pilot / local pilot 的判断
- API 调用与状态归一化
- snapshot 跳转
- 命令复制

子组件负责：

- 统一结果卡片模板
- status / output / readiness 文案
- error type 与 execution detail 格式化
- copy button 文案和事件透出

兼容性边界：

- `最近 LangGraph Precheck` 文案保持不变。
- `最近 LangGraph External Pilot` 文案保持不变。
- `最近 LocalFakeFramework Pilot` 文案保持不变。
- `复制修复命令` / `复制快照命令` 文案保持不变。
- `查看时间线` 事件仍由父组件执行路由跳转。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1 passed`
- `22 passed`

### 第三轮拆分（2026-05-13）

已继续拆分单个 adapter 健康卡片。

新增：

- `frontend-vue/src/components/AdapterHealthCard.vue`

子组件覆盖：

- adapter 标题、状态、adapter_id、adapter_type、detail。
- configuration / execution mode / package / runtime 标签。
- required package / missing package / required env / missing env 标签。
- execution block reason 展示。
- precheck / external pilot / local fake pilot 操作入口。
- 三类 pilot 结果卡片组合。

父组件保留：

- adapter health contract 归一化。
- precheck / external pilot / local pilot 的 API 调用。
- planner 刷新、profile 重载和错误态处理。
- snapshot 路由跳转与快照命令复制。
- 当前 external pilot failure distribution 的路由激活态。

兼容性边界：

- adapter 卡片展示文案保持不变。
- precheck / external pilot / local pilot 按钮文案保持不变。
- `AdapterPilotResultCard` 的事件仍由父组件统一接收并执行副作用。
- 新组件只负责展示和事件透出，不持有 runtime API 副作用。

当前文件规模：

- `RuntimeSurfacePanel.vue`：约 1538 行
- `AdapterHealthCard.vue`：约 378 行
- `AdapterExternalPilotFailureSummary.vue`：约 266 行
- `AdapterPilotResultCard.vue`：约 364 行

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1 passed`
- `22 passed`

### E-5：整理文档入口

建议新增：

- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/architecture/extension_points.md`
- `docs/roadmap/next_phase_hardening.md`

`docs/change` 保留为审计日志，不再承担唯一 onboarding 入口。

### 实施状态（2026-05-13）

已完成。

新增：

- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/architecture/extension_points.md`
- `docs/roadmap/next_phase_hardening.md`

同步更新：

- `docs/README.md`

当前文档分工：

- `docs/architecture/current_architecture.md`：记录当前四层架构、已收口能力、仍为 draft 的能力和架构约束。
- `docs/architecture/runtime_contracts.md`：记录 Runtime Surface 当前 contract、来源文件和维护约束。
- `docs/architecture/extension_points.md`：记录垂域智能体、工具、MCP、Skill/Memory、外部框架 Adapter、治理策略和前端治理台的接入 seam。
- `docs/roadmap/next_phase_hardening.md`：记录 Phase E 之后的推荐硬化顺序。

兼容性边界：

- 未移动旧文档。
- 未删除 `docs/change` 中的阶段日志。
- `docs/change` 继续作为历史审计日志；`docs/architecture` 作为当前事实入口。

### E-6：Embedded SDK 最小闭环

已完成第一刀。

调整：

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_command_registry_service.py`
- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

当前状态：

- `create_run` 从 draft boundary 升级为 preview。
- `stream_events` 从 draft boundary 升级为 preview。
- `submit_approval` 从 draft boundary 升级为 preview。
- `register_tool` 仍保持 draft boundary。
- `resume_run` 在 E-9 已推进为 preview boundary。

实现边界：

- 当前 SDK 是 in-process memory runtime，不承诺跨进程持久化。
- `create_run` 会创建 `AgentRunContext` 并写入 `run_created` 事件。
- payload 带 `approval_request` 时会复用 `ApprovalEngineService` 创建正式 `ApprovalRequestState`。
- `submit_approval` 会更新 approval 状态，并写入 `approval_resolved` 和 Runtime Core 状态迁移事件。
- SDK 不接入主 chat 路径，不绕过 Runtime Core / ApprovalEngine。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_command_registry_service -v
```

结果：

- `Ran 6 tests`
- `OK`

### E-7：Governance Timeline 前端瘦身第一刀

已完成第一轮拆分。

新增：

- `frontend-vue/src/components/GovernanceTimelineFilters.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineFilters.test.js`

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`

拆分边界：

- 父组件继续负责 timeline 数据构造、路由过滤、snapshot、payload、remediation 和复制动作。
- `GovernanceTimelineFilters.vue` 只负责风险模式与事件来源两组 chip 展示。
- 过滤器通过 `v-model:active-severity` / `v-model:active-filter` 与父组件同步，不持有 timeline 数据。

兼容性边界：

- `button.filter-chip` / `button.severity-chip` class 保持不变。
- 原有过滤点击行为保持不变。
- 原有路由驱动过滤行为保持不变。

当前文件规模：

- `GovernanceTimelinePanel.vue`：约 2470 行
- `GovernanceTimelineFilters.vue`：约 74 行

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineFilters.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- `GovernanceTimelineFilters.test.js`：`1 passed`
- `GovernanceTimelinePanel.test.js`：`38 passed`

已完成第二轮拆分。

新增：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`

拆分边界：

- 父组件继续负责 timeline 数据构造、路由过滤、snapshot 定位、payload 展开状态和复制副作用。
- `GovernanceTimelineEventCard.vue` 只负责单条事件展示、snapshot 引用展示、payload 摘要 / JSON 展示和按钮事件透出。
- 子组件不读取路由、不访问 store、不直接写剪贴板，所有副作用仍由父组件统一治理。

兼容性边界：

- `timeline-item`、`severity-*`、`payload-toggle-btn` 等关键 class 保持不变。
- 原有 payload 展开 / 收起、snapshot ref 复制、snapshot command 复制、payload 复制行为保持不变。
- 原有路由驱动过滤、snapshot 聚焦高亮和 warning scope 行为保持不变。

当前文件规模：

- `GovernanceTimelinePanel.vue`：约 2367 行
- `GovernanceTimelineFilters.vue`：约 74 行
- `GovernanceTimelineEventCard.vue`：约 194 行

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- `GovernanceTimelineEventCard.test.js`：`1 passed`
- `GovernanceTimelinePanel.test.js`：`38 passed`
- 合计：`39 passed`

### E-8：Agent Harness Facade 最小入口

本轮目标不是重写 `backend/harness/agent_harness.py` 主循环，而是在 `agent_framework` 层补一个面向垂域项目的高层开发者入口，让后续业务接入不必直接操作 scheduler / trace / approval store。

新增：

- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_agent_harness_facade.py`

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/__init__.py`
- `backend/services/command_registry_service.py`
- `tests/agent_framework/test_command_registry_service.py`

当前入口：

```python
from backend.agent_framework import create_agent

agent = create_agent(name="fraud_assistant", model_name="doubao")
result = agent.run("评估这条交易是否存在诈骗风险")
events = list(agent.stream(result["run"]["run_id"]))
```

拆分边界：

- `AgentHarnessFacade` 只负责开发者友好的 `run / stream / approve` 入口。
- 实际运行状态、事件流和 approval 仍委托给 `EmbeddedAgentRuntimeSDK`。
- SDK 继续复用 `AgentRunContext`、`AgentEventFactory`、`ApprovalEngineService`。
- Facade 不直接调用 LangGraph / DeepAgents / CrewAI 等外部框架，也不成为第二套 Runtime Core。

兼容性边界：

- `EmbeddedAgentRuntimeSDK.create_run()` 增加 `metadata / input` 透传，不改变已有 create / stream / approval 行为。
- Command runtime contract 新增 `agent_harness_facade` 字段，保留原有 `embedded_sdk` 字段。
- `register_tool / resume_run / delegate / artifact workspace` 暂不在本轮实现，继续作为下一阶段 harness 体验补强项。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_agent_harness_facade -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_command_registry_service tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk -v
C:\Users\dddsg\miniconda3\python.exe -m py_compile backend/agent_framework/harness.py backend/agent_framework/sdk.py backend/agent_framework/__init__.py
```

结果：

- `test_agent_harness_facade`：`2 passed`
- `test_command_registry_service + test_agent_harness_facade + test_embedded_runtime_sdk`：`8 passed`
- `py_compile`：通过

### E-9：SDK / Facade Resume 最小闭环

本轮把 `resume_run` 从 draft 推进到 preview，但只实现状态恢复信号，不假装已经接入真实 LLM 执行循环。

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `tests/agent_framework/test_command_registry_service.py`

行为边界：

- `EmbeddedAgentRuntimeSDK.resume_run(run_id)` 仅允许从 `observing` 状态恢复。
- 恢复后进入下一次 `generating` iteration，并把 `stop_reason` 标记为 `run_resumed`。
- 恢复过程写入 `run_resumed` status event 与 state event。
- `init`、`waiting_approval`、`done` 等非 ready 状态不会被误恢复。
- `AgentHarnessFacade.resume(run_id)` 只代理 SDK，不直接操作 runtime state。

兼容性边界：

- `register_tool` 仍是 draft boundary。
- `resume_run` 当前不是完整执行循环，只是让 harness 层具备 approval 后继续执行的状态入口。
- Command runtime contract 中 `resume_run` 与 `resume` 均标记为 preview。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service -v
```

结果：

- 合计：`10 passed`

### E-10：SDK / Facade Delegate Child Run 最小闭环

本轮把 `delegate_run` 作为 preview 能力补入 SDK 与 Facade，用于建立 parent run 与 child run 的对象关系和事件关系。它不是完整 subagent executor，不负责并行调度、上下文预算、结果 merge 或模型执行。

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `tests/agent_framework/test_command_registry_service.py`

行为边界：

- `EmbeddedAgentRuntimeSDK.delegate_run(parent_run_id, payload)` 要求 parent run 已存在。
- child run 默认使用 `run_kind=child`，并继承 parent 的 `conversation_id / user_id / model_name`。
- child run 写入 `parent_run_id`、`parent_agent_name` 等 metadata。
- parent run 事件流写入 `child_run_created`，并包含 `child_run_id` 与 child run snapshot。
- `AgentHarnessFacade.delegate(parent_run_id, payload, name=...)` 只补开发者友好的 child agent metadata，然后代理 SDK。

兼容性边界：

- `delegate_run` 只创建 child run，不自动调用真实 LLM / tool 执行。
- 父子 run 的结果汇总、失败传播、并行执行、上下文隔离仍留给后续 child executor 阶段。
- Command runtime contract 中 `delegate_run` 与 `delegate` 均标记为 preview。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service -v
```

结果：

- 合计：`12 passed`

### E-11：SDK / Facade Artifact 最小闭环

本轮补入内存态 artifact 引用能力，用于让长任务、评估结果、工具副产物具备可审计承载点。它不是完整 workspace，不负责真实文件写入、目录隔离或持久化存储。

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `tests/agent_framework/test_command_registry_service.py`

行为边界：

- `EmbeddedAgentRuntimeSDK.create_artifact(run_id, payload)` 要求 run 已存在。
- artifact 默认使用 `memory://runs/{run_id}/artifacts/{artifact_id}` URI。
- artifact 写入 `run_id / parent_run_id / conversation_id / kind / content / metadata`。
- run snapshot 的 `metadata.artifacts` 会追加轻量 artifact ref。
- run 事件流写入 `artifact_created`，包含 artifact 与 artifact ref。
- `AgentHarnessFacade.create_artifact(...)` 只补充当前 agent metadata，并代理 SDK。

兼容性边界：

- artifact 当前为 in-process memory 引用，不承诺跨进程持久化。
- 本轮不写真实文件系统，不创建 workspace 目录。
- 后续真实 workspace 应接入 `ArtifactStore` 或独立 workspace service，而不是把文件 IO 写进 Facade。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service -v
```

结果：

- 合计：`14 passed`

### E-12：SDK ArtifactStore 注入边界

本轮把 E-11 的纯内存 artifact 引用推进为可插拔 `ArtifactStore` 边界。默认仍保留 memory URI 行为；当 SDK 显式注入 artifact store 时，`create_artifact` 会优先通过 store 创建 artifact，再统一写入 run metadata 与事件流。

调整：

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`

行为边界：

- `EmbeddedAgentRuntimeSDK(..., artifact_store=store)` 支持注入符合 `ArtifactStore` 协议的对象。
- 注入 store 后，`create_artifact` 会调用 `store.create_artifact(...)`。
- 返回的 artifact 使用 `artifact://{artifact_id}` URI，表示来自 artifact store，而不是 SDK 内部 memory URI。
- run metadata 与 `artifact_created` event 仍使用统一 artifact dict / artifact ref 结构。
- 未注入 store 时，继续使用 `memory://runs/{run_id}/artifacts/{artifact_id}`，保证嵌入式最小运行不依赖数据库。

兼容性边界：

- Facade 不直接依赖 `ArtifactStore`，仍只代理 SDK。
- 本轮不创建 workspace 目录，不处理真实文件 IO。
- SQLAlchemy artifact store 是否用于生产，由服务层创建 SDK 时注入，不在 SDK 内部隐式拉数据库。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service tests.agent_framework.test_adapters tests.agent_framework.test_artifacts -v
C:\Users\dddsg\miniconda3\python.exe -m py_compile backend/agent_framework/harness.py backend/agent_framework/sdk.py backend/agent_framework/adapters.py backend/agent_framework/artifacts.py backend/services/command_registry_service.py
```

结果：

- `test_embedded_runtime_sdk`：`9 passed`
- 相关后端测试合计：`17 passed`
- `py_compile`：通过

### E-13：SDK / Facade Artifact Replay 最小入口

本轮在 E-12 的 artifact store 注入边界之上，补入 `list_artifacts` 查询入口，用于按 run 回放已关联 artifact。它是治理台和审计 replay 的最小查询契约，不负责跨 run 搜索、权限判断或文件系统读取。

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `tests/agent_framework/test_command_registry_service.py`

行为边界：

- `EmbeddedAgentRuntimeSDK.list_artifacts(run_id)` 要求 run 已存在。
- replay 顺序沿用 run metadata 中 `artifacts` refs 的创建顺序。
- 如果 SDK artifact index 中存在完整 artifact dict，则返回完整 artifact；否则返回轻量 artifact ref。
- `AgentHarnessFacade.list_artifacts(run_id)` 只代理 SDK。

兼容性边界：

- 不跨 run 查询 artifact。
- 不从真实文件系统读取 artifact 内容。
- 不做权限过滤，后续服务化 API 需要在 router/service 层补鉴权。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service tests.agent_framework.test_adapters tests.agent_framework.test_artifacts -v
C:\Users\dddsg\miniconda3\python.exe -m py_compile backend/agent_framework/harness.py backend/agent_framework/sdk.py backend/agent_framework/adapters.py backend/agent_framework/artifacts.py backend/services/command_registry_service.py
```

结果：

- SDK / Facade / Command contract：`16 passed`
- 相关后端测试合计：`18 passed`
- `py_compile`：通过

## 6. Phase F：Harness Runtime Loop

Phase F 的目标是把当前 preview harness 从“开发者入口集合”推进到“有统一执行循环 seam 的运行层”。本阶段仍然保持克制：先收口 loop controller，不直接接真实 LLM、真实工具调用、反思评审或复杂降级。

### F-1：ExecutionLoopController 最小执行循环

本轮新增 `ExecutionLoopController`，作为后续 tool execution、reflection、review、fallback policy 和真实 child executor 的挂接 seam。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `tests/agent_framework/test_command_registry_service.py`

行为边界：

- `ExecutionLoopController.run_until_stop(...)` 驱动 run 经过 `planning -> generating -> observing -> finalizing -> done`。
- 每个步骤写入 Runtime Core state event。
- 非终态步骤写入 `execution_loop_step` status event。
- 完成时写入 `done` event，`status_kind = execution_loop_done`。
- `EmbeddedAgentRuntimeSDK.execute_run(run_id)` 负责把 loop 事件追加到 SDK 事件流。
- `AgentHarnessFacade.execute(run_id)` 只代理 SDK。

兼容性边界：

- 当前不调用真实 LLM。
- 当前不执行工具。
- 当前不做 reflection / reviewer。
- 当前不做 fallback / retry / model degrade。
- 当前不调度真实 child executor。
- 后续能力必须挂到 `ExecutionLoopController` 的 step / policy seam，而不是塞进 Facade。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_command_registry_service -v
```

结果：

- Execution Loop / SDK / Facade / Command contract：`19 passed`

### F-2：Execution Loop Reviewer Gate

本轮在 F-1 的最小循环上补入 reviewer gate，让执行循环在 `finalizing` 阶段具备可插拔质量门禁。它不是内置 LLM reviewer，也不是完整反思系统；它只是把“评审结果如何影响 run 状态”变成一等可测试规则。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_agent_harness_facade.py`

行为边界：

- 新增 `ExecutionReviewResult`，规范 reviewer 输出：`reviewer / status / summary / findings / metadata`。
- `ExecutionLoopController(..., reviewer=callable)` 会在 `finalizing` 阶段调用 reviewer。
- reviewer 结果写入 `run.metadata.execution_review`。
- reviewer 通过时写入 `execution_loop_reviewed`，并继续进入 `done`。
- reviewer 返回 `status = rejected` 时，run 转为 `failed`，`stop_reason = review_rejected`。
- reviewer 拒绝时写入 `execution_loop_review_rejected` error event，且不再写 `execution_loop_done`。
- `EmbeddedAgentRuntimeSDK.execute_run(run_id, reviewer=...)` 与 `AgentHarnessFacade.execute(run_id, reviewer=...)` 均可透传 reviewer。

兼容性边界：

- 当前 reviewer 是 callable seam，不内置模型调用。
- 当前不做多轮 reflection。
- 当前不自动修复 reviewer 发现的问题。
- 当前不做风险分级路由或人工审批升级。
- 后续 LLM reviewer / rubric evaluator / fallback policy 应挂到该 reviewer seam，而不是写入 Facade。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_command_registry_service -v
```

结果：

- Execution Loop / Facade / SDK / Command contract：`22 passed`

### F-3：Execution Loop Fallback Seam

本轮在 reviewer gate 之后补入 fallback seam，让 loop 内部 callable 抛错时不再变成散落异常，而是进入统一可审计降级规则。当前优先覆盖 reviewer 异常；后续真实 LLM step、tool step、reflection step 也应复用该 seam。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_agent_harness_facade.py`

行为边界：

- 新增 `ExecutionFallbackResult`，规范 fallback 输出：`strategy / status / summary / metadata`。
- reviewer 抛错且未提供 fallback handler 时，默认 fail-closed。
- fail-closed 时 run 转为 `failed`，`stop_reason = loop_exception`。
- fail-closed 写入 `metadata.execution_fallback` 与 `execution_loop_failed` error event。
- 提供 fallback handler 且返回 `status = handled` 时，写入 `execution_loop_fallback_applied`，并继续后续 loop。
- `EmbeddedAgentRuntimeSDK.execute_run(..., fallback_handler=...)` 与 `AgentHarnessFacade.execute(..., fallback_handler=...)` 均可透传 fallback handler。

兼容性边界：

- 当前 fallback handler 是 callable seam，不内置模型切换、重试或备用工具调用。
- fallback 默认不静默吞错；没有显式 handled 结果时必须失败。
- 当前只覆盖 loop callable 异常，不处理进程崩溃、跨进程恢复或持久化补偿。
- 后续 retry / model degrade / tool fallback / human escalation 应挂到该 fallback seam。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_command_registry_service -v
```

结果：

- Execution Loop / Facade / SDK / Command contract：`25 passed`

### F-4：Execution Loop Reflection / Revise Seam

本轮补入 reflector seam，让 loop 在 `observing` 后可以记录反思结果，并在明确请求 `revise` 时回到 `generating` 开启下一轮 iteration。这是后续接入 LLM self-reflection、rubric evaluator 或业务规则复核的基础，但当前仍不做真实模型调用和自动修复。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_agent_harness_facade.py`

行为边界：

- 新增 `ExecutionReflectionResult`，规范 reflector 输出：`reflector / status / summary / observations / metadata`。
- reflector 在 `observing` 后执行。
- reflector 结果追加到 `run.metadata.execution_reflections`。
- 每次 reflection 写入 `execution_loop_reflected` event。
- reflector 返回 `status = revise` 且当前 iteration 小于 `max_iterations` 时，写入 `execution_loop_revision_requested`。
- revision 会回到 `generating` step，开启下一轮 iteration。
- `EmbeddedAgentRuntimeSDK.execute_run(..., reflector=..., max_iterations=...)` 与 `AgentHarnessFacade.execute(..., reflector=..., max_iterations=...)` 均可透传。

兼容性边界：

- 当前 reflector 是 callable seam，不内置 LLM self-reflection。
- 当前 revision 不修改 prompt / input / memory，只负责 loop 控制。
- 当前 `max_iterations` 默认仍为 1，避免无意中引入长循环。
- 当前不自动把 observations 转成工具调用或修复计划。
- 后续真实 reflection / critique / repair 应挂到该 reflector seam。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_command_registry_service -v
```

结果：

- Execution Loop / Facade / SDK / Command contract：`28 passed`

### F-5：Execution Loop Tool Executor Seam

本轮补入 tool executor seam，让 loop 在 `generating` 后可以进入明确的 act 阶段。当前只表达工具调用结果、事件和 `tool_history`，不接真实 tool registry、权限审批或沙箱执行。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_agent_harness_facade.py`

行为边界：

- 新增 `ExecutionToolResult`，规范 tool executor 输出：`tool_name / args / result / tool_call_id / execution`。
- tool executor 在 `generating` 后执行。
- tool executor 返回结果时，run 进入 `tool_calling` 状态。
- loop 写入 `tool_call_start` 与 `tool_result` event。
- loop 调用 `AgentRunContext.record_tool_result(...)`，把工具结果写入 `run.tool_history`。
- `EmbeddedAgentRuntimeSDK.execute_run(..., tool_executor=...)` 与 `AgentHarnessFacade.execute(..., tool_executor=...)` 均可透传。

兼容性边界：

- 当前 tool executor 是 callable seam，不内置 ToolRuntimeService。
- 当前不自动做 tool schema validation。
- 当前不自动触发 approval / permission policy。
- 当前不做工具重试、超时、沙箱或文件系统隔离。
- 后续真实 tool execution 应接入 ToolRuntimeService、ApprovalEngine、PolicyEngine 和 fallback seam。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_command_registry_service -v
```

结果：

- Execution Loop / Facade / SDK / Command contract：`30 passed`

### F-6：Execution Loop Tool Policy / Approval Gate Seam

本轮在 tool executor 前补入 tool policy seam，让 loop 可以在工具执行前被治理策略拦截。当前只把 run 暂停到 `waiting_approval`，不创建正式 `ApprovalRequestState`；后续再接 ApprovalEngine / PolicyEngine。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_agent_harness_facade.py`

行为边界：

- 新增 `ExecutionToolDecision`，规范 tool policy 输出：`status / tool_name / reason / metadata`。
- tool policy 在 `generating` 后、tool executor 前执行。
- tool policy 返回 `approval_required` 时，run 转入 `waiting_approval`。
- 暂停时 `stop_reason = tool_approval_required`。
- loop 写入 `tool_permission_required` event。
- approval_required 时不会调用 tool executor，不会写入 `tool_result`，也不会写入 `execution_loop_done`。
- `EmbeddedAgentRuntimeSDK.execute_run(..., tool_policy=...)` 与 `AgentHarnessFacade.execute(..., tool_policy=...)` 均可透传。

兼容性边界：

- 当前 tool policy 是 callable seam，不内置 PolicyEngine。
- 当前不创建正式 `ApprovalRequestState`。
- 当前不接 UI 人工审批流。
- 当前不在审批后自动恢复 tool execution。
- 后续应把 `tool_policy` 接到 PolicyEngine / ApprovalEngine，并让 `resume_run` 接回 ExecutionLoopController 恢复点。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop tests.agent_framework.test_agent_harness_facade tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_command_registry_service -v
```

结果：

- Execution Loop / Facade / SDK / Command contract：`32 passed`

### F-7：Execution Tool Policy Approval Lifecycle

本轮把 F-6 的 preview permission seam 进一步接入正式治理对象：`approval_required` 不再只是暂停状态，而是由 Embedded SDK 转成正式 `ApprovalRequestState`；同时补齐 `denied` fail-closed 语义，并提供 PolicyEngine 到 Execution Loop 的 adapter。

调整：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/sdk.py`
- `backend/agent_framework/tool_policy.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_execution_loop.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `tests/agent_framework/test_execution_tool_policy_adapter.py`
- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `ExecutionToolDecision` 新增显式 `tool_args`，避免审批对象只能拿到工具名而丢失参数。
- `tool_policy` 返回 `approval_required` 时，Execution Loop 仍只负责暂停与事件；Embedded SDK 负责创建正式 `ApprovalRequestState`。
- SDK 会把审批对象写入 `_approvals`，并回填 `run.metadata.approval_request_id` 与 `run.metadata.approval_request`。
- SDK 会追加 `approval_created` event，Facade 可直接通过 `agent.approve(approval_request_id, "approved")` 提交审批。
- `tool_policy` 返回 `denied` 时，run 进入 `failed`，`stop_reason = tool_policy_denied`，写入 `tool_permission_denied` error event，不会调用 tool executor，也不会写入 done。
- 新增 `build_policy_engine_tool_policy(...)`，把 `PolicyEngineService.evaluate_tool_use()` 映射为 `ExecutionToolDecision`：`allowed / approval_required / denied`。

兼容性边界：

- `ExecutionLoopController` 仍不直接依赖 `ApprovalEngineService` 或 `PolicyEngineService`，避免 Runtime Core 反向依赖服务层。
- 当前审批通过后只恢复到现有 `submit_approval()` 的 `observing` 状态，还不会自动回到原 tool execution 断点。
- 当前仍未接入真实 ToolRuntimeService、工具 schema validation、沙箱隔离、工具超时和 retry。
- 下一步应设计 resume-after-approval continuation，让审批通过后能安全恢复被暂停的 tool call。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_execute_run_creates_formal_approval_when_tool_policy_requires_it -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_agent_harness_facade.AgentHarnessFacadeTests.test_execute_tool_policy_approval_can_be_submitted_through_facade -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_loop.ExecutionLoopControllerTests.test_tool_policy_denied_fails_closed_before_tool_execution -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_execution_tool_policy_adapter -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_agent_harness_facade.AgentHarnessFacadeTests.test_execute_can_use_policy_engine_tool_policy_adapter -v
```

结果：

- SDK formal approval lifecycle：`1 passed`
- Facade approval submit：`1 passed`
- Execution Loop denied fail-closed：`1 passed`
- PolicyEngine adapter：`2 passed`
- Facade policy adapter integration：`1 passed`

### F-8：Approval Resume Tool Continuation

本轮把 F-7 的审批对象进一步接到工具恢复执行：当 `execute_run` 因 tool policy `approval_required` 暂停，并且调用方传入了 tool executor 时，Embedded SDK 会登记一个内存态 continuation；审批通过后，`submit_approval()` 会消费该 continuation 执行原工具，并写入标准工具事件。

调整：

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `execute_run(..., tool_policy=..., tool_executor=...)` 在审批暂停时会把 tool executor 暂存为内存态 continuation。
- `submit_approval(approval_request_id, "approved")` 会消费 continuation，写入 `tool_approval_continued` status event。
- 审批通过后会继续写入 `tool_call_start` / `tool_result`，并把工具结果记录到 `run.tool_history`。
- 工具执行后 run 回到 `observing`，`stop_reason = approval_approved`，为后续 observing / finalizing continuation 留出边界。
- `submit_approval(..., "denied")` 会丢弃 pending continuation，并在 metadata 中标记 `tool_approval_continuation.status = discarded`。

兼容性边界：

- 当前 continuation 是进程内 callable，不做跨进程持久化；服务重启后不能恢复。
- 当前只恢复 tool execution，不自动继续跑完整 `observing -> finalizing -> done` loop。
- 当前不接真实 ToolRuntimeService、工具 schema validation、沙箱隔离、工具超时和 retry。
- 后续应把 continuation 改造成可持久化 descriptor，并让 `resume_run` 或专门的 continuation runner 接回后续 loop。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_submit_approval_resumes_pending_tool_execution_when_approved -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_denied_approval_discards_pending_tool_continuation -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_agent_harness_facade.AgentHarnessFacadeTests.test_execute_tool_policy_approval_can_be_submitted_through_facade -v
```

结果：

- SDK approved continuation resume：`1 passed`
- SDK denied continuation discard：`1 passed`
- Facade approval resume：`1 passed`

### F-9：Resume Loop Continuation

本轮把 F-8 停在 `observing` 的工具审批恢复链路继续向后接入最小 loop continuation。默认 `resume_run()` 行为保持不变，仍是状态恢复信号；新增显式 `continue_loop=True`，用于从 `observing` 接回 `observing -> finalizing -> done`，避免审批后工具执行完成但 run 生命周期无法收口。

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `EmbeddedAgentRuntimeSDK.resume_run(run_id)` 默认行为不变：仍从 `observing` 恢复到下一次 `generating` iteration。
- `EmbeddedAgentRuntimeSDK.resume_run(run_id, continue_loop=True)` 会从 `observing` 接回 `observing / finalizing / done` 子循环。
- `AgentHarnessFacade.resume(run_id, continue_loop=True)` 透传该能力，Facade 不自行拼接 Runtime Core 状态。
- `execute_run` 因 approval pause 保存的 reflector / reviewer / fallback handler / max_iterations 会作为内存态 loop continuation 被复用。
- `continue_loop=True` 不会重新进入 `generating`，也不会再次触发 tool policy / tool executor。
- continuation loop 会继续写入 `execution_loop_reflected`、`execution_loop_reviewed`、`execution_loop_done` 等标准事件。

兼容性边界：

- 当前 loop continuation 仍是进程内 callable，不做跨进程持久化。
- 当前只覆盖 `observing -> finalizing -> done` 后半段，不处理 revise 后重新生成的复杂路径。
- 如果没有保存 reviewer / reflector continuation，也可完成默认后半段 loop，但不会产生额外评审/反思结果。
- 后续应把 continuation descriptor 持久化，并补 retry / failure recovery / trace timeline 聚合。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_resume_run_can_continue_loop_after_approved_tool_execution -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_agent_harness_facade.AgentHarnessFacadeTests.test_resume_can_continue_loop_after_tool_approval -v
```

结果：

- SDK resume loop continuation：`1 passed`
- Facade resume loop continuation：`1 passed`

### F-10：Observable Continuation Descriptor

本轮把 F-8 / F-9 中藏在 SDK 内存结构里的 continuation 状态同步到 run metadata，形成可被治理台、审计和排障读取的 descriptor。该 descriptor 不等于持久化恢复能力，但能先解决“运行为什么停在这里、后续是否还可恢复、是否已被消费/拒绝”的可观测性问题。

调整：

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `docs/architecture/current_architecture.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `execute_run` 因 tool approval pause 创建审批对象时，会写入 `run.metadata.loop_continuation.status = pending`。
- descriptor 会记录 `resume_mode = observing_to_done`、`request_id`、`source = tool_approval_required`。
- descriptor 会记录是否存在 reflector / reviewer / fallback handler continuation，方便治理台提示后续恢复能力。
- `resume_run(..., continue_loop=True)` 成功消费后，会写入 `run.metadata.loop_continuation.status = consumed`。
- 审批被拒绝时，会把 `tool_approval_continuation` 与 `loop_continuation` 都标记为 `discarded`。

兼容性边界：

- descriptor 仍保存在 run metadata 内，不是跨进程持久化 continuation。
- 当前不序列化 callable，只暴露可观测状态和恢复模式。
- 后续如果做持久化 continuation，应在该 descriptor 基础上增加 `continuation_id / persistence_backend / retry_policy / failure_count` 等字段。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_execute_run_creates_formal_approval_when_tool_policy_requires_it tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_resume_run_can_continue_loop_after_approved_tool_execution -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_denied_approval_discards_pending_tool_continuation -v
```

结果：

- SDK continuation descriptor pending / consumed：`2 passed`
- SDK continuation descriptor discarded：`1 passed`

### F-11：Continuation Lifecycle Events

本轮把 F-10 的 continuation descriptor 从“当前状态可见”推进到“生命周期可审计”。metadata 负责回答当前 continuation 是什么状态，event stream 负责回答它什么时候注册、什么时候消费、什么时候丢弃。

调整：

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- loop approval pause 创建 descriptor 后，会追加 `loop_continuation_registered` status event。
- `resume_run(..., continue_loop=True)` 消费后，会追加 `loop_continuation_consumed` status event。
- 审批拒绝丢弃 continuation 后，会追加 `loop_continuation_discarded` status event。
- 三类事件 payload 都携带 `loop_continuation` descriptor 快照。
- `execution_loop_done` 仍保持为成功完成 loop 的最后事件，避免破坏现有 done 事件消费习惯。

兼容性边界：

- 当前事件只表达内存态 continuation 生命周期，不代表跨进程持久化。
- 后续 Governance Timeline 可直接消费这些 `status_kind`，不需要从 metadata diff 里反推出生命周期。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_execute_run_creates_formal_approval_when_tool_policy_requires_it tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_resume_run_can_continue_loop_after_approved_tool_execution tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_denied_approval_discards_pending_tool_continuation -v
```

结果：

- SDK continuation lifecycle events：`3 passed`

### F-12：Embedded SDK Event Contract Surface

本轮把 F-11 新增的 continuation 生命周期事件纳入 Embedded SDK runtime contract。此前事件已经写入流，但治理台、审计服务和垂域项目只能“知道代码里有这些事件”；现在可以通过 `build_embedded_sdk_contract().event_status_kinds` 发现事件面。

调整：

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_command_registry_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `build_embedded_sdk_contract()` 新增 `event_status_kinds`。
- 每个事件声明 `status_kind / event_type / category / stability / required_payload`。
- 目前纳入 preview contract 的类别包括：`run`、`approval`、`execution_loop`、`tool`、`continuation`。
- continuation 三个生命周期事件均标记为 preview：`loop_continuation_registered`、`loop_continuation_consumed`、`loop_continuation_discarded`。
- `CommandRegistryService.build_runtime_contract()` 会透传该 SDK contract，前端和治理服务无需单独导入 SDK 模块。

兼容性边界：

- 该 contract 只声明事件面，不保证事件持久化 backend。
- 后续新增/删除 `status_kind` 需要同步 contract、测试和 `docs/change`。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_command_registry_service.CommandRegistryServiceTests.test_runtime_contract_exposes_command_definitions_and_sdk_interface -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_sdk_contract_declares_minimal_embedded_methods -v
```

结果：

- Command Registry SDK event contract：`1 passed`
- Embedded SDK event contract：`1 passed`

### F-13：Runtime Contract Snapshot Guard for SDK Event Surface

本轮把 F-12 暴露的 `event_status_kinds` 纳入 runtime contract snapshot guard。这样事件面不是“文档说有”，而是会被 contract snapshot 检查；如果后续删掉 `command_contract.embedded_sdk.event_status_kinds`，runtime profile 会退化为 degraded，smoke / 治理门禁可以拦住。

调整：

- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_contract_smoke.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `RuntimeContractSnapshotService` 支持点路径 required field，例如 `embedded_sdk.event_status_kinds`。
- `command_contract` required fields 新增 `embedded_sdk.event_status_kinds`。
- snapshot stable fields 会记录嵌套字段路径，便于治理台定位具体缺失字段。
- `runtime_contract_smoke` 的健康 stub 对齐该事件契约字段。

兼容性边界：

- 当前 snapshot guard 只检查字段存在和 shape，不校验每个 `status_kind` 的完整枚举。
- 后续如要更严格，可增加 allowlist/required status_kind 检查，例如必须包含 `loop_continuation_registered / consumed / discarded`。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_snapshot_service -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_smoke -v
```

结果：

- Runtime contract snapshot nested event field guard：`2 passed`
- Runtime contract smoke：`3 passed`

### F-14：Required SDK Event Status Kind Guard

本轮把 F-13 的字段存在性检查升级为关键枚举检查：`event_status_kinds` 字段存在还不够，必须包含 continuation 生命周期三件套，否则 contract snapshot 也会退化为 degraded。

调整：

- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `ContractSnapshotSpec` 新增 `required_status_kinds`。
- `command_contract.embedded_sdk.event_status_kinds` 必须包含：
  - `loop_continuation_registered`
  - `loop_continuation_consumed`
  - `loop_continuation_discarded`
- snapshot 顶层新增 `missing_status_kind_count`。
- 单个 contract snapshot 新增 `missing_status_kinds` 与 `missing_status_kind_count`。
- fingerprint 会纳入缺失 status_kind，避免事件枚举漂移时 fingerprint 不变。

兼容性边界：

- 当前只强制 continuation 生命周期三件套。
- 后续可以继续把 `execution_loop_done`、`approval_created`、`approval_resolved` 等纳入必需枚举，但需要先确认前端和审计服务的消费稳定性。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_snapshot_service -v
```

结果：

- Runtime contract snapshot required status_kind guard：`3 passed`

### F-15：Core SDK Event Status Kind Guard

本轮把 F-14 的 continuation-only 枚举护栏扩展到审批生命周期和 run 完成边界。现在 `event_status_kinds` 字段存在还不够，必须同时包含审批创建、审批处理、执行完成和 continuation 生命周期事件。

调整：

- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `command_contract.embedded_sdk.event_status_kinds` 现在必须包含：
  - `approval_created`
  - `approval_resolved`
  - `execution_loop_done`
  - `loop_continuation_registered`
  - `loop_continuation_consumed`
  - `loop_continuation_discarded`
- 如果缺少审批或完成边界事件，snapshot 顶层 `overall_status` 会退化为 `degraded`。
- `missing_status_kinds` 会保留具体缺失列表，便于治理台定位。

兼容性边界：

- 当前仍只校验关键事件枚举是否存在，不校验每个事件的 payload schema 深度一致性。
- 后续可进一步把 `required_payload` 纳入 snapshot guard，但需要先确认事件 payload 结构稳定。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_snapshot_service -v
```

结果：

- Runtime contract snapshot core status_kind guard：`4 passed`

### F-16：SDK Event Required Payload Guard

本轮把 F-15 的事件枚举护栏继续推进到关键 payload 字段。现在 `event_status_kinds` 不只是要保留关键 `status_kind`，每个关键事件还必须声明稳定的 `required_payload`，避免后续重构时事件名还在、但治理台和审计服务真正依赖的字段被静默删掉。

调整：

- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `ContractSnapshotSpec` 新增 `required_event_payloads`。
- `command_contract.embedded_sdk.event_status_kinds` 的关键事件现在必须声明：
  - `approval_created`：`approval_request_id`、`approval_request`
  - `approval_resolved`：`approval_request_id`、`approval_request`、`decision`
  - `execution_loop_done`：`run`、`completed_steps`
  - `loop_continuation_registered`：`loop_continuation`
  - `loop_continuation_consumed`：`loop_continuation`
  - `loop_continuation_discarded`：`loop_continuation`
- snapshot 顶层新增 `missing_event_payload_count`。
- 单个 contract snapshot 新增 `missing_event_payloads` 与 `missing_event_payload_count`。
- fingerprint 会纳入缺失 payload 字段，避免 payload 契约漂移时 fingerprint 不变。

兼容性边界：

- 当前只校验关键事件的必需 payload 字段存在，不做深层 schema 校验。
- 如果某个 `status_kind` 本身缺失，由已有 `missing_status_kinds` 报告；payload guard 不重复计数，避免治理告警噪音。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_snapshot_service -v
```

结果：

- Runtime contract snapshot required payload guard：`5 passed`

### F-17：SDK Event Payload Sample Validator

本轮把 F-16 的“契约声明护栏”再往真实运行样本推进一步：新增 SDK 事件 payload 诊断函数，用同一份 `event_status_kinds.required_payload` 校验真实事件流，避免出现“contract 声明正确，但 SDK 实际发出的事件少字段”的隐性漂移。

调整：

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/__init__.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 新增 `validate_embedded_sdk_event_payloads(events, contract=None)`。
- 只检查 SDK contract 已声明的 `status_kind`，未知事件不误伤。
- 返回 `valid / checked_event_count / missing_payload_count / missing_payloads`。
- `missing_payloads` 保留事件下标、`status_kind` 和缺失字段，方便 smoke 或治理台定位。
- 已用真实 SDK 生命周期覆盖：
  - `run_created`
  - `approval_created`
  - `approval_resolved`
  - `loop_continuation_registered`
  - `loop_continuation_consumed`
  - `loop_continuation_discarded`
  - `execution_loop_step`
  - `execution_loop_done`
  - `tool_approval_continued`

兼容性边界：

- 该 validator 只校验顶层字段存在，不校验字段内部 schema。
- 不改变 SDK 事件格式，不改变现有运行路径。
- 可后续接入 runtime contract smoke，让 smoke 同时检查 profile contract 与真实事件样本。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_sdk_event_payload_validator_reports_missing_required_payload_fields -v
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_embedded_runtime_sdk.EmbeddedAgentRuntimeSDKTests.test_sdk_emitted_lifecycle_events_match_declared_required_payloads -v
```

结果：

- SDK event payload validator red/green：`2 passed`
- 相关 harness / SDK / snapshot / smoke 回归：`61 passed`

### F-18：Runtime Contract Smoke SDK Event Payload Gate

本轮把 F-17 的 SDK event payload validator 接入 `runtime_contract_smoke`。现在 smoke 不只检查 runtime profile contract snapshot 与 framework adapter pilot，还会构造一组真实 Embedded SDK 生命周期事件样本，并用 `validate_embedded_sdk_event_payloads(...)` 校验实际事件是否满足 SDK contract 的 `required_payload` 声明。

调整：

- `backend/scripts/runtime_contract_smoke.py`
- `tests/agent_framework/test_runtime_contract_smoke.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- smoke 新增 `embedded_sdk_event_payloads` 检查项。
- 检查样本覆盖直接完成、审批通过后 continuation consumed、审批拒绝后 continuation discarded 三条路径。
- 输出包含 `event_count / checked_event_count / missing_payload_count / missing_payloads`。
- 如果真实事件样本缺少 SDK contract 声明的必需 payload，smoke 返回 `fail`。

兼容性边界：

- 不依赖外部服务，不写文件，只使用内存态 `EmbeddedAgentRuntimeSDK`。
- 不改变 API 响应结构，只扩展 smoke 输出的 checks 列表。
- 当前仍只校验顶层 payload 字段存在，不做深层 schema 检查。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_smoke -v
```

结果：

- Runtime contract smoke SDK event payload gate：`4 passed`
- 相关 harness / SDK / snapshot / smoke 回归：`62 passed`

### F-19：Quality Gate Runtime Contract Check Summary

本轮把 `runtime_contract_smoke` 的结构化 checks 接入 `quality_gate_report.py`。此前质量门禁报告只保留 step 级别 stdout/stderr，机器可以回放，但不方便直接读取 `embedded_sdk_event_payloads` 这类子检查；现在 report 会解析 smoke JSON，并在 Markdown summary 中展示 Runtime Contract Checks。

调整：

- `backend/scripts/quality_gate_report.py`
- `tests/agent_framework/test_quality_gate_report.py`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `_run_step(...)` 会尝试解析 JSON stdout。
- 如果 stdout 是包含 `checks` 的结构化 smoke 输出，step 结果会新增：
  - `structured_output`
  - `contract_checks`
- `_render_summary(...)` 会新增 `## Runtime Contract Checks` 表格。
- 表格展示 step、check、PASS/FAIL、failure reason。

兼容性边界：

- 非 JSON stdout 不受影响。
- 原有 step 级别 `passed / stdout / stderr` 保持不变。
- 当前只做报告聚合，不改变质量门禁执行顺序和失败判定。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_quality_gate_report -v
```

结果：

- Quality gate runtime contract check summary：`2 passed`
- 相关 harness / SDK / snapshot / smoke / quality gate report 回归：`64 passed`

### F-20：Runtime Surface Contract Gate Summary

本轮把 F-19 产出的 `contract_checks` 健康摘要接入 Runtime Surface 后端 profile。`/api/runtime-profile` 现在会暴露 `runtime_contract_gate`，用于让前端治理台、CI artifact 消费方或后续自动分析直接读取最近一次质量门禁中的 Runtime Contract Checks 状态。

调整：

- `backend/services/runtime_contract_gate_service.py`
- `backend/services/runtime_surface_service.py`
- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_contract_gate_service.py`
- `tests/agent_framework/test_runtime_surface_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`

行为边界：

- `RuntimeContractGateService` 默认只读取 `quality-gate-report.json`。
- 不在 `/api/runtime-profile` 请求中重新执行 `runtime_contract_smoke.py`。
- profile 新增 `runtime_contract_gate`：
  - `contract_version`
  - `available`
  - `overall_status`
  - `check_count`
  - `failed_check_count`
  - `failure_reason`
  - `checks`
- `runtime_contract_snapshot_service.py` 已把 `runtime_contract_gate` 纳入 required contracts，避免后续字段静默漂移。

兼容性边界：

- 如果质量门禁报告不存在，`runtime_contract_gate.overall_status = unknown`，并返回 `quality_gate_report_missing`。
- 如果报告存在但没有 `contract_checks`，状态为 `unknown`，并返回 `contract_checks_missing`。
- 如果存在失败 check，状态为 `degraded`。
- 所有 checks 只做轻量归一化，不改变 F-19 的 quality gate report 原始结构。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_runtime_contract_snapshot_service tests.agent_framework.test_quality_gate_report -v
```

结果：

- Runtime contract gate summary：`11 passed`

### F-21：Runtime Surface Contract Gate Panel

本轮把 F-20 暴露到后端 profile 的 `runtime_contract_gate` 接入 Runtime Surface 前端治理台。治理台现在可以直接展示最近一次质量门禁报告中的 Runtime Contract Checks 健康状态，不需要用户从 smoke stdout 或 markdown summary 里手动定位。

调整：

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`

行为边界：

- 新增 `Contract Gate` 卡片，展示：
  - `overall_status`
  - `check_count`
  - `failed_check_count`
  - `available`
  - `generated_at`
  - `report_path`
  - `failure_reason`
- checks 明细逐项展示 `step / name / passed|failed / failure_reason`。
- 对 `contract_snapshot_status / adapter_health_status / checked_event_count / missing_payload_count` 做轻量展示。

兼容性边界：

- 前端只消费 `runtime_contract_gate`，不触发 quality gate 或 smoke 执行。
- 如果后端 profile 暂未提供该 contract，页面显示 `等待后端接入 runtime_contract_gate`。
- 不新增独立 API，不改变 Runtime Surface profile 原有字段。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- Runtime Surface Contract Gate panel：`23 passed`

### F-22：Runtime Surface Top-Level Contract Gate Signal

本轮把 F-21 的 Contract Gate 明细状态提升到 Runtime Surface 顶部摘要区。用户打开运行时能力面后，可以第一眼看到契约门禁整体状态与失败检查数，不需要滚动到 `Contract Gate` 卡片才能发现质量门禁退化。

调整：

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`

行为边界：

- 顶部 summary 新增 `契约门禁` 卡片。
- 展示 `runtime_contract_gate.overall_status`。
- 展示 `failed checks: <failed_check_count>`。
- 详细 checks 仍保留在 F-21 的 `Contract Gate` 卡片中。

兼容性边界：

- 不新增 API，不改变后端 contract。
- 如果后端没有 `runtime_contract_gate`，顶部摘要显示 `-` 与 `failed checks: 0`。
- 不触发 quality gate 或 smoke 执行，只消费 Runtime Surface profile。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- Runtime Surface top-level contract gate signal：`24 passed`

### F-23：Runtime Contract Gate Governance Timeline Entry Point

本轮把 F-22 的顶部契约门禁信号接入治理时间线入口。Runtime Surface 顶部 `契约门禁` 卡片在存在失败检查时会显示 `查看治理事件`，点击后进入 Governance Timeline 的 `runtime_contract + warning` 过滤视图。

调整：

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`

行为边界：

- Runtime Surface 顶部摘要新增 `查看治理事件` 按钮。
- 按钮仅在 `runtime_contract_gate.failed_check_count > 0` 时展示。
- 点击后跳转：
  - `tab=advanced`
  - `governance_filter=runtime_contract`
  - `governance_severity=warning`
- Governance Timeline 新增 `runtime_contract` domain label：`Runtime Contract`。
- Governance Timeline 过滤顺序中加入 `runtime_contract`，用于承接后续真实质量门禁治理事件。

兼容性边界：

- 不新增后端 API。
- 不伪造真实后端治理事件；本轮只固定前端入口与 domain 协议。
- 如果当前时间线没有 `runtime_contract` 事件，路由过滤仍保持稳定，不影响其他域。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Runtime Surface + Governance Timeline contract gate entry point：`64 passed`

### F-24：Runtime Contract Gate Degraded Trace Recording

本轮把 F-23 固定的前端入口接上后端真实事件记录。`GET /api/runtime-profile` 现在可以携带 `conversation_id / plan_id / item_id` 上下文；当 `runtime_contract_gate.overall_status = degraded` 且调用方提供了运行上下文时，后端会向当前治理时间线写入 `runtime_contract_gate_degraded` trace。

调整：

- `backend/routers/health.py`
- `frontend-vue/src/api/index.js`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `tests/agent_framework/test_health_router.py`

行为边界：

- `runtime-profile` 支持可选 query：
  - `conversation_id`
  - `plan_id`
  - `item_id`
- 当 `runtime_contract_gate.overall_status = degraded` 且存在上下文时，写入 trace：
  - `source = runtime_contract`
  - `event_type = runtime_contract_gate_degraded`
  - `severity = warning`
  - `summary = Runtime contract gate degraded`
  - `detail = failed_check_count=<n>`
- payload 包含：
  - `snapshot_ref`
  - `contract_version`
  - `overall_status`
  - `available`
  - `generated_at`
  - `report_path`
  - `check_count`
  - `failed_check_count`
  - `failure_reason`
  - `failed_checks`
- 响应在实际写入成功时追加 `runtime_contract_gate_timeline_recording`。
- Runtime Surface 前端拉取 profile 时会传入当前 conversation / plan / active item 上下文。

兼容性边界：

- 无上下文的普通 `/api/runtime-profile` 请求仍只读 profile，不写治理时间线。
- 非 degraded 状态不写 trace。
- 不新增独立 API，不改变原有 profile 字段。
- 记录失败不会阻断 profile 的基本读取；测试覆盖了成功写入路径。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js src/services/__tests__/commands.test.js
```

结果：

- Backend runtime contract gate trace recording：`24 passed`
- Frontend runtime surface / governance timeline context bridge：`66 passed`

### F-25：Runtime Contract Gate Trace Dedupe

本轮对 F-24 的 degraded trace 写入增加进程内 fingerprint 去重。Runtime Surface 前端会周期性刷新 `/api/runtime-profile`，如果每次读取同一个 degraded `runtime_contract_gate` 都写入治理时间线，会把真实问题淹没在重复事件里。F-25 的目标是保留第一次可审计事件，同时避免重复刷新污染 Governance Timeline。

调整：

- `backend/routers/health.py`
- `tests/agent_framework/test_health_router.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- degraded gate 写 trace 前会生成稳定 fingerprint。
- fingerprint 输入包含：
  - `conversation_id`
  - `plan_id`
  - `item_id`
  - `contract_version`
  - `overall_status`
  - `report_path`
  - `check_count`
  - `failed_check_count`
  - `failure_reason`
  - failed checks 的关键失败字段
- 同一上下文、同一失败签名重复读取时：
  - 不再追加新的 `runtime_contract_gate_degraded` trace
  - 响应返回 `runtime_contract_gate_timeline_recording.trace_written = false`
  - 响应返回 `reason = duplicate_runtime_contract_gate_trace`
- 同一上下文下，如果失败签名发生变化，例如失败 check 数量或失败 check 名称变化，会再次写入新的治理 trace。

兼容性边界：

- 本轮是进程内去重，不是跨进程、跨重启的持久化去重。
- 不新增前端行为，不改变 `runtime_contract_gate` profile contract。
- 不影响非 degraded、无上下文或 trace target missing 的原有保护分支。
- fingerprint 只选取稳定失败字段，避免把无关展示字段变化误判为新的治理事件。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Runtime contract gate trace dedupe：`26 passed`

### F-26：Runtime Contract Gate Persisted Trace Dedupe

本轮把 F-25 的进程内去重向持久化治理记录推进了一步。`runtime_contract_gate_degraded` trace payload 现在会写入稳定 `fingerprint`；后续 Runtime Surface 再次读取 degraded gate 时，后端会先查询同一运行上下文下已有的 runtime contract trace，命中相同 fingerprint 则不再重复写入。

调整：

- `backend/services/run_trace_service.py`
- `backend/routers/health.py`
- `tests/agent_framework/test_health_router.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 首次写入 `runtime_contract_gate_degraded` trace 时，payload 包含 `fingerprint`。
- 写入前先检查：
  - 进程内 `_RUNTIME_CONTRACT_GATE_TRACE_FINGERPRINTS`
  - 当前运行上下文下已持久化的 `runtime_contract / runtime_contract_gate_degraded` trace payload fingerprint
- 命中进程内缓存时：
  - `reason = duplicate_runtime_contract_gate_trace`
  - `dedupe_source = memory`
- 命中历史 trace 时：
  - `reason = duplicate_runtime_contract_gate_trace`
  - `dedupe_source = persisted_trace`
- 历史 trace 查询通过 `RunTraceService.has_runtime_trace_fingerprint(...)` 暴露为窄口径 seam，避免在 router 中直接耦合 planner / scheduler runtime store 细节。

兼容性边界：

- 不新增数据库表，不改变现有 trace 存储格式，只在 payload 中补充 `fingerprint` 字段。
- 只查询同一 runtime target 下的最近 trace 样本，避免全局扫描。
- 如果无法解析 target、user 或历史 trace，仍按原逻辑继续尝试写入，不阻断 Runtime Profile 读取。
- 这一步已经可覆盖服务重启后的重复识别；多实例并发下仍可能存在竞态，后续如需强一致可再引入唯一索引或专用治理事件去重表。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Runtime contract gate persisted trace dedupe：`27 passed`

### F-27：Runtime Contract Gate Dedupe Key Contract

本轮把 F-26 的 `fingerprint` 去重能力提升为更明确的治理事件去重 contract。`runtime_contract_gate_degraded` trace payload 和 profile recording 现在都会暴露 `dedupe_key`，格式为 `runtime_contract_gate_degraded:<fingerprint>`。这让后续如果需要做数据库唯一索引、专用治理事件去重表或跨实例强一致写入，可以直接复用稳定字段，而不是重新解释业务 payload。

调整：

- `backend/services/run_trace_service.py`
- `backend/routers/health.py`
- `tests/agent_framework/test_health_router.py`
- `tests/agent_framework/test_run_trace_service.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `runtime_contract_gate_timeline_recording` 新增：
  - `dedupe_key`
- `runtime_contract_gate_degraded` trace payload 新增：
  - `dedupe_key`
- `RunTraceService.has_runtime_trace_fingerprint(...)` 支持：
  - 优先用 `dedupe_key` 判断重复
  - 对 F-26 之前只写入 `fingerprint` 的历史 trace 保持 fallback 兼容
- `fingerprint` 仍保留，继续作为可观测、可调试的稳定摘要。

兼容性边界：

- 不改变既有 `fingerprint` 语义。
- 不新增数据库 schema。
- 不把强一致并发控制塞进 router；本轮只固定 dedupe contract。
- 旧 trace 没有 `dedupe_key` 时仍可按 `fingerprint` 命中。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_run_trace_service tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Runtime contract gate dedupe key contract：`44 passed`

### F-28：Generic Runtime Trace Dedupe Key Seam

本轮把 F-27 的 `dedupe_key` 从 Runtime Contract Gate 局部实现抽成 `RunTraceService` 的通用治理 trace 幂等 seam。后续 doctor、framework adapter precheck、external pilot、remediation action 等治理事件，如果需要避免重复写入 Governance Timeline，可以直接通过 `has_runtime_trace_dedupe_key(...)` 查询历史事件，而不用复制 runtime contract gate 的 fingerprint 查询逻辑。

调整：

- `backend/services/run_trace_service.py`
- `backend/routers/health.py`
- `tests/agent_framework/test_run_trace_service.py`
- `tests/agent_framework/test_health_router.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `RunTraceService` 新增通用查询：
  - `has_runtime_trace_dedupe_key(...)`
- `has_runtime_trace_fingerprint(...)` 保留为兼容层，并复用同一个内部 payload match 实现。
- Runtime Contract Gate 写 trace 前优先调用 `has_runtime_trace_dedupe_key(...)`。
- Runtime Contract Gate 仍保留 fingerprint fallback，用于兼容 F-26 之前已经写入但没有 `dedupe_key` 的历史 trace。
- 新增内部 helper：
  - `_has_runtime_trace_payload_match(...)`
  - 统一处理 target 解析、trace 过滤、payload 字段匹配。

兼容性边界：

- 不改变现有 `append_runtime_trace(...)`。
- 不要求所有治理事件立刻写 `dedupe_key`。
- 不新增数据库 schema。
- 当前仍是“查询后写入”的幂等保护，不是数据库级唯一约束；多实例强一致仍需要后续唯一键/索引或事务保护。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_run_trace_service tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Generic runtime trace dedupe key seam：`45 passed`

### F-29：Doctor Gate Failed Dedupe Key Adoption

本轮把 F-28 抽出的通用 `has_runtime_trace_dedupe_key(...)` seam 接入第二个治理事件：`doctor_gate_failed`。这样 Runtime Contract Gate 不再是唯一消费者，幂等能力开始从单点功能变成治理时间线的通用写入约束。

调整：

- `backend/routers/health.py`
- `tests/agent_framework/test_health_router.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `doctor_gate_failed` 现在生成稳定 `dedupe_key`：
  - `doctor_gate_failed:<conversation_id>:<scope>:<exit_code>:<non_closed_action_count>`
- 写入 `doctor_gate_failed` trace / audit 前，会先调用：
  - `RunTraceService.has_runtime_trace_dedupe_key(...)`
- 首次 gate failed：
  - 正常写入 trace
  - 正常写入 audit
  - payload 携带 `dedupe_key`
- 重复 gate failed：
  - 不再重复写入 `doctor_gate_failed` trace
  - 不再重复写入 `doctor_gate_failed` audit
  - `timeline_recording.trace_gate_failed = false`
  - `timeline_recording.gate_failed_dedupe_source = persisted_trace`
- `doctor_run_started` 与 `doctor_run_completed` 仍保持每次运行都记录，因为它们代表真实执行历史，不按 gate failure dedupe。

兼容性边界：

- 只对 `doctor_gate_failed` 去重，不影响 Doctor 基础 run trace。
- 不新增 API 字段依赖；新增的 `gate_failed_dedupe_key` / `gate_failed_dedupe_source` 仅增强 `timeline_recording` 的可观测性。
- 当前 dedupe key 先覆盖 capability gap 类门禁失败的主要重复场景；如后续 Doctor report 增加更细粒度失败类型，可扩展 key 的签名字段。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_run_trace_service tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Doctor gate failed dedupe key adoption：`46 passed`

### F-30：Framework Adapter Precheck Dedupe Key Adoption

本轮把通用 `dedupe_key` seam 接入第三条治理链路：Framework Adapter precheck。`framework_adapter_precheck_completed` 通常会在缺包、缺环境变量、运行开关关闭时被反复触发；如果每次都写入 Governance Timeline，会把真正状态变化淹没在重复预检记录里。

调整：

- `backend/services/framework_adapter_timeline_service.py`
- `tests/agent_framework/test_framework_adapter_runtime_service.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `framework_adapter_precheck_completed` payload 新增稳定 `dedupe_key`：
  - `framework_adapter_precheck_completed:<conversation_id>:<adapter_id>:<configuration_status>:<execution_block_reason|detail>`
- 写入 precheck trace / audit 前，会先调用：
  - `RunTraceService.has_runtime_trace_dedupe_key(...)`
- 首次 precheck：
  - 正常写入 trace
  - 正常写入 audit
  - `timeline_recording.trace_written = true`
  - `timeline_recording.audit_written = true`
  - payload 携带 `dedupe_key`
- 重复 precheck：
  - 不再重复写入 trace
  - 不再重复写入 audit
  - `timeline_recording.trace_written = false`
  - `timeline_recording.audit_written = false`
  - `timeline_recording.dedupe_source = persisted_trace`

兼容性边界：

- 不影响 adapter runtime pilot / external pilot 的事件流记录。
- 不改变 precheck API 的核心 readiness 字段。
- 只对同一 adapter、同一配置状态、同一阻断原因去重；如果缺失项或阻断原因变化，会生成新的 dedupe key 并记录新事件。
- 当前仍依赖 trace payload 查询，不是数据库唯一约束。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_runtime_service_external_pilot tests.agent_framework.test_run_trace_service tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Framework adapter precheck dedupe key adoption：`62 passed`

### F-31：Framework Adapter External Error Dedupe Key Adoption

本轮把通用 `dedupe_key` seam 接入 Framework Adapter external pilot 的失败事件：`framework_adapter_external_error`。这样框架适配器治理链路已经覆盖配置预检失败与外部运行失败两类高频重复事件。

调整：

- `backend/services/framework_adapter_timeline_service.py`
- `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `framework_adapter_external_error` trace payload 新增稳定 `dedupe_key`：
  - `framework_adapter_external_error:<conversation_id>:<adapter_id>:<error_type>:<detail>`
- `_append_run_events(...)` 只对 `framework_adapter_external_error` 做 dedupe。
- 命中已有同类 external error 时：
  - 不再重复写入 external error trace
  - 仍保留 external pilot completed audit，用于表达确实发生了一次 pilot 执行尝试
- 成功 external pilot 的 status / reasoning / output 事件不做 dedupe，保持完整运行记录。
- 普通 local fake framework adapter run 事件不受影响。

兼容性边界：

- 不改变 external pilot API 返回结构。
- 不影响外部错误分类逻辑。
- dedupe key 以 `error_type + detail` 作为失败签名；如果错误详情变化，会记录新的治理事件。
- 当前仍是 trace payload 查询式幂等，不是数据库唯一约束。

已执行：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_runtime_service_external_pilot tests.agent_framework.test_run_trace_service tests.agent_framework.test_health_router tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_runtime_surface_service -v
```

结果：

- Framework adapter external error dedupe key adoption：`63 passed`

### F-32：Governance Timeline Dedupe Key Visibility

本轮把后端已经写入 trace payload 的 `dedupe_key` 暴露到 Governance Timeline 事件卡片。此前幂等能力已经覆盖 Runtime Contract Gate、Doctor Gate Failed、Framework Adapter Precheck、Framework Adapter External Error，但前端只能在展开 Payload 后看到完整字段。F-32 在事件卡片上增加轻量“幂等键”提示，让治理台能直接识别哪些事件具备幂等签名。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当 `entry.payload.dedupe_key` 存在时，事件卡片展示：
  - `幂等键 <dedupe_key preview>`
- 展示文本会截断到 72 字符，完整 `dedupe_key` 仍可通过展开 Payload 查看。
- 不改变 Governance Timeline 数据加载、过滤、复制 Payload、复制 Snapshot 的行为。
- 不要求所有事件都有 `dedupe_key`；没有该字段的历史事件保持原展示。

兼容性边界：

- 这是纯展示增强，不新增后端 API。
- 只消费 payload 中已有字段，不推断或重新计算 dedupe key。
- 对 Runtime Contract、Doctor、Framework Adapter 等已接入 dedupe key 的事件统一生效。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
```

结果：

- Governance timeline dedupe key visibility：`1 passed`

### F-33：Governance Timeline Dedupe Key Copy Action

本轮在 F-32 的可见性基础上，为 Governance Timeline 事件卡片增加 `dedupe_key` 复制能力。治理排查时，维护者可以直接复制幂等签名，用于比对重复事件、编写 issue、定位 trace payload，不再需要展开 Payload 后手动截取字段。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当 `entry.payload.dedupe_key` 存在时，事件卡片新增：
  - `复制幂等键`
- 复制成功后短暂显示：
  - `已复制幂等键`
- 复制内容为完整 `dedupe_key`，不是前端截断预览。
- 复制失败时复用治理台错误提示：
  - `当前环境不支持复制幂等键`
- 不影响 Payload 展开、复制 Payload、复制快照引用、复制快照命令。

兼容性边界：

- 没有 `dedupe_key` 的历史事件不显示该按钮。
- 不新增后端 API。
- 不改变现有 payload JSON 结构。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven filter and payload expansion"
```

结果：

- Governance timeline event card dedupe copy：`1 passed`
- Governance timeline panel dedupe copy integration：`1 passed`

### F-34：Governance Timeline Dedupe Key Route Focus

本轮把 F-32/F-33 已经可见、可复制的 `dedupe_key` 接入 Governance Timeline 路由过滤。维护者复制当前治理视图后，可以通过 `governance_dedupe_key=<key>` 直接回放到同一个幂等事件集合，用于 issue、CI artifact、跨 trace 排查和重复事件定位。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 新增路由查询参数：
  - `governance_dedupe_key=<dedupe_key>`
- Timeline 过滤顺序保持为：
  - severity -> domain -> framework adapter error type -> dedupe key -> snapshot
- `governance_dedupe_key` 对 `entry.payload.dedupe_key` 做严格匹配；没有匹配事件时显示空结果，不回退到未过滤事件。
- `复制当前视图` 生成的链接会包含 `governance_dedupe_key`。
- `复制当前视图` 生成的文本会包含：
  - `幂等键: <dedupe_key>`

兼容性边界：

- 不新增后端 API。
- 不重新计算 dedupe key，只消费 trace payload 中已有字段。
- 没有 `dedupe_key` 的历史事件不会被该路由参数命中。
- 现有 `governance_filter`、`governance_severity`、`governance_error_type`、`governance_snapshot` 行为保持兼容。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven dedupe key filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline route-driven dedupe key focus：`1 passed`
- Governance timeline dedupe key regression：`2 passed, 41 passed`

### F-35：Governance Timeline Dedupe Key Focus Clear Action

本轮补齐 F-34 的可用性闭环：当 Governance Timeline 通过 `governance_dedupe_key` 路由参数进入幂等键聚焦状态时，页面顶部 summary 区会明确显示当前幂等键聚焦，并提供一键清除动作。这样维护者可以从复制链接进入精确事件视图，再快速回到同一 domain 下的完整事件集合。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当 `activeDedupeKey` 存在时，summary 区展示：
  - `幂等键聚焦`
  - 截断后的 `dedupe_key` 预览
  - `清除幂等键`
- 点击 `清除幂等键` 后：
  - 清空本地 `activeDedupeKey`
  - 通过已有 watcher 移除路由中的 `governance_dedupe_key`
  - 保留当前 `governance_filter` / `governance_severity` / `governance_error_type` 等其他聚焦状态
- 幂等键预览使用中间截断，避免长 key 撑开 summary 卡片。

兼容性边界：

- 不改变 F-34 的严格匹配过滤语义。
- 不新增后端 API。
- 不影响事件卡片级 `复制幂等键`。
- 不改变 `复制当前视图` 对 `governance_dedupe_key` 的输出。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "clears route-driven dedupe key focus"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe key clear focus：`1 passed`
- Governance timeline dedupe key focus regression：`2 passed, 42 passed`

### F-36：Governance Timeline Dedupe Key Empty Focus State

本轮补齐 `governance_dedupe_key` 路由聚焦的异常可解释性：当复制的幂等键链接过期、目标事件不在当前会话计划中，或 trace payload 不再包含对应 `dedupe_key` 时，统一事件流不再只显示空列表，而是明确说明当前幂等键没有匹配到治理事件，并提供清除入口。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当 `activeDedupeKey` 存在且 `filteredTimeline.length === 0` 时，统一事件流显示空状态：
  - `当前幂等键没有匹配到治理事件`
  - 当前 `dedupe_key`
  - `清除幂等键聚焦`
- 点击 `清除幂等键聚焦` 后复用 `clearDedupeKeyFilter()`，移除 `governance_dedupe_key` 并保留其他路由过滤条件。
- 有匹配事件时不显示空状态，保持 F-34/F-35 的正常聚焦视图。

兼容性边界：

- 不改变 dedupe key 严格匹配语义。
- 不改变事件卡片渲染和复制能力。
- 不新增后端 API。
- 空状态只服务于 dedupe key 聚焦；普通 domain/severity/filter 无结果暂不扩展。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "explains empty route-driven dedupe key focus"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe key empty focus state：`1 passed`
- Governance timeline empty focus regression：`2 passed, 43 passed`

### F-37：Governance Timeline Event Dedupe Key Focus Action

本轮把 F-34 到 F-36 的幂等键路由聚焦能力前置到事件卡片操作区。维护者看到带 `dedupe_key` 的治理事件后，可以直接点击 `聚焦幂等键`，无需手动复制 key 或拼接 URL 参数，即可进入当前幂等签名的精确事件视图。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当事件存在 `entry.payload.dedupe_key` 时，事件卡片新增：
  - `聚焦幂等键`
- 点击后：
  - EventCard emit `focus-dedupe-key`
  - Panel 设置 `activeDedupeKey`
  - 复用既有 watcher 写入 `governance_dedupe_key`
  - 复用 F-34 的严格过滤逻辑刷新事件列表
- 聚焦动作保留当前 domain/severity/error type 等上下文。

兼容性边界：

- 不影响 `复制幂等键`。
- 不改变 `复制当前视图` 行为。
- 没有 `dedupe_key` 的历史事件不显示该操作。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "focuses timeline by dedupe key"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline event dedupe focus action：`1 passed`
- Governance timeline panel dedupe focus action：`1 passed`
- Governance timeline dedupe focus regression：`2 passed, 44 passed`

### F-38：Governance Timeline Dedupe Focus Active State

本轮补齐 F-37 的状态反馈：当事件卡片对应的 `dedupe_key` 已经是当前 `governance_dedupe_key` 聚焦目标时，卡片操作区不再继续展示可点击的 `聚焦幂等键`，而是展示禁用态 `已聚焦幂等键`。这样维护者可以直接判断当前列表已经处于该幂等签名视图，避免重复点击和状态歧义。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- EventCard 新增 `focusedDedupeKey` prop。
- Panel 按 `activeDedupeKey === getTimelineDedupeKey(entry)` 传入该状态。
- 当 `focusedDedupeKey = true` 时：
  - 按钮文案为 `已聚焦幂等键`
  - 按钮禁用
  - 不再 emit `focus-dedupe-key`
- 当 `focusedDedupeKey = false` 时：
  - 保持 F-37 的 `聚焦幂等键` 行为。

兼容性边界：

- 不影响 `复制幂等键`。
- 不改变 route-driven dedupe key 过滤语义。
- 不改变空状态、summary 清除、复制当前视图行为。
- 没有 `dedupe_key` 的历史事件仍不显示该按钮。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "focuses timeline by dedupe key"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe focus active state card：`2 passed`
- Governance timeline dedupe focus active state panel：`1 passed`
- Governance timeline dedupe focus active state regression：`2 passed, 45 passed`

### F-39：Governance Timeline Active Dedupe Key Copy

本轮把当前 `governance_dedupe_key` 聚焦状态补成可复制对象。此前事件卡片可以复制单条事件的 `dedupe_key`，但当用户从路由链接进入聚焦视图、或当前 key 对应事件已经被过滤为空状态时，summary 区只能查看和清除，不能直接复制当前 active key。F-39 在 `幂等键聚焦` summary 卡片上增加复制当前 key 的动作。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当 `activeDedupeKey` 存在时，summary 卡片新增：
  - `复制当前幂等键`
- 点击后复制完整 `activeDedupeKey`，不是截断预览。
- 复制成功后短暂显示：
  - `已复制当前幂等键`
- 复制失败时复用错误提示：
  - `当前环境不支持复制幂等键`
- 复制状态使用独立 `copiedActiveDedupeKey`，不影响事件卡片级 `copiedDedupeKey`。

兼容性边界：

- 不改变事件卡片 `复制幂等键`。
- 不改变 `聚焦幂等键` / `已聚焦幂等键`。
- 不改变 route-driven filtering、summary clear 和 empty state。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "copies active route-driven dedupe key"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline active dedupe key copy：`1 passed`
- Governance timeline active dedupe key copy regression：`2 passed, 46 passed`

### F-40：Governance Timeline Active Dedupe Copy State Reset

本轮修复 F-39 引入后的一个状态一致性细节：当用户复制当前 active `dedupe_key` 后，立即清除并聚焦另一个 `dedupe_key`，summary 卡片不应继续沿用旧 key 的 `已复制当前幂等键` 状态。F-40 在 `activeDedupeKey` 变化时主动重置 summary 级复制状态和 timer。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 新增 `resetCopiedActiveDedupeKey()`。
- 当 `activeDedupeKey` 从一个值切换到另一个值，或被清空时：
  - 清理 `copiedActiveDedupeKeyResetTimer`
  - 将 `copiedActiveDedupeKey` 置为 `false`
- `onUnmounted` 复用该 reset helper，避免重复 timer 清理逻辑。
- 切换到新 key 后，summary 按钮回到：
  - `复制当前幂等键`

兼容性边界：

- 不改变 clipboard 写入逻辑。
- 不影响事件卡片级 `复制幂等键` 状态。
- 不改变 route-driven filtering、empty state、focus action。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "resets active dedupe key copied state"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline active dedupe copy state reset：`1 passed`
- Governance timeline active dedupe copy state reset regression：`2 passed, 47 passed`

### F-41：Governance Timeline Dedupe Key Match Count

本轮提升 `governance_dedupe_key` 聚焦状态的可解释性：`幂等键聚焦` summary 卡片新增匹配事件数，让维护者可以直接看到当前 key 在当前过滤范围内命中了多少条事件，以及该范围内总共有多少候选事件。此前只能从统一事件流的 `最近 N / M` 间接推断。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `幂等键聚焦` summary 卡片新增：
  - `匹配事件 N / M`
- `N` 为当前 `activeDedupeKey` 过滤后的 `filteredTimeline.length`。
- `M` 为当前 severity / domain / framework adapter error type 过滤后的 dedupe 候选事件数。
- 提取 `dedupeCandidateTimeline` computed，避免 dedupe 过滤前候选范围的计算逻辑重复。

兼容性边界：

- 不改变 dedupe key 严格匹配语义。
- 不改变 snapshot fallback 行为。
- 不改变复制、聚焦、清除、空状态。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven dedupe key filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe key match count：`1 passed`
- Governance timeline dedupe key match count regression：`2 passed, 47 passed`

### F-42：Governance Timeline Dedupe Match Count in Copied View

本轮把 F-41 的 `匹配事件 N / M` 写入 `复制当前视图` 的文本快照。这样治理视图被粘贴到 issue、CI artifact 或排查记录时，不只包含 `governance_dedupe_key` 和完整 `dedupe_key`，还包含该 key 在当前过滤范围内的命中比例。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 当 `activeDedupeKey` 存在时，`buildCurrentViewSnapshot()` 输出：
  - `幂等键: <activeDedupeKey>`
  - `幂等键匹配: 匹配事件 N / M`
- `N / M` 复用 F-41 的 `activeDedupeKeyMatchLabel`，避免 UI 与复制文本使用不同计算口径。
- URL 仍继续包含 `governance_dedupe_key`。

兼容性边界：

- 不改变复制当前视图的链接生成。
- 不改变 summary 展示。
- 不改变 dedupe key 过滤、聚焦、清除、复制当前 key。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven dedupe key filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe match count copied view：`1 passed`
- Governance timeline dedupe match count copied view regression：`2 passed, 47 passed`

### F-43：Governance Timeline Event Dedupe Key Middle Truncation

本轮优化事件卡片上的 `dedupe_key` 预览。此前长 key 只保留前 72 个字符，容易丢掉末尾错误详情；而 Framework Adapter external error 的 `dedupe_key` 尾部通常包含 `detail`，对排查很关键。F-43 改为中间截断，同时保留事件类型 / adapter 前缀和错误详情尾部。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- EventCard 新增本地 `truncateMiddle()` helper。
- 长 `dedupe_key` 预览从前缀截断改为中间截断：
  - 保留前缀签名和 adapter 标识
  - 保留尾部错误详情
- 预览长度上限调整为 96 字符，提升可读性。
- 完整 key 仍通过 `复制幂等键` / `复制当前幂等键` 获取。

兼容性边界：

- 不改变 payload、route query 或复制内容。
- 不改变 summary 中的 active dedupe key 预览。
- 不影响 `聚焦幂等键` 和 `已聚焦幂等键`。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline event dedupe key middle truncation：`2 passed`
- Governance timeline event dedupe key middle truncation regression：`2 passed, 47 passed`

### F-44：Governance Timeline Event Dedupe Key Full Tooltip

本轮在 F-43 的中间截断基础上，补齐事件卡片 `dedupe_key` 预览的完整可访问信息。长 key 在视觉上仍保持中间截断，但 badge 会通过 `title` 和 `aria-label` 暴露完整 key，方便悬停查看，也让辅助技术能读取完整幂等签名。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `.timeline-dedupe-key` 新增：
  - `title="<full dedupe_key>"`
  - `aria-label="幂等键 <full dedupe_key>"`
- 显示文本仍使用 F-43 的中间截断预览。
- 完整 key 仍可通过 `复制幂等键` / `复制当前幂等键` 获取。

兼容性边界：

- 不改变 DOM 结构层级。
- 不改变复制、聚焦、过滤、路由行为。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline event dedupe key full tooltip：`2 passed`
- Governance timeline event dedupe key full tooltip regression：`2 passed, 47 passed`

### F-45：Governance Timeline Dedupe Focus Full Tooltip

本轮把 F-44 的完整 key 可访问性补齐到顶部 `幂等键聚焦` summary 卡片。当前 active `dedupe_key` 仍按中间截断展示，避免撑开 summary 区；同时通过 `title` 和 `aria-label` 暴露完整 key，便于悬停查看、辅助技术读取以及 UI 测试稳定断言。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `.dedupe-focus-preview` 新增：
  - `title="<active dedupe_key>"`
  - `aria-label="幂等键聚焦 <active dedupe_key>"`
- 显示文本仍使用既有 `activeDedupeKeyPreview` 中间截断逻辑。
- 复制当前幂等键、清除幂等键、路由过滤、匹配事件数不变。

兼容性边界：

- 不改变事件卡片级 `dedupe_key` 展示。
- 不改变复制当前视图内容。
- 不新增后端 API。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven dedupe key filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe focus full tooltip：`1 passed`
- Governance timeline dedupe focus full tooltip regression：`2 passed, 47 passed`

### F-46：Governance Timeline Dedupe Focus Button Full Tooltip

本轮继续补齐事件卡片的幂等键可访问闭环。F-44 已让 `dedupe_key` 预览 badge 暴露完整 key，F-46 进一步让 `聚焦幂等键` / `已聚焦幂等键` 按钮也通过 `title` 和 `aria-label` 携带完整 key。这样维护者在只聚焦操作区时，也能明确该按钮将作用于哪个幂等签名。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `聚焦幂等键` 按钮新增：
  - `title="<dedupe_key>"`
  - `aria-label="聚焦幂等键 <dedupe_key>"`
- `已聚焦幂等键` 禁用态按钮新增：
  - `title="<dedupe_key>"`
  - `aria-label="已聚焦幂等键 <dedupe_key>"`
- 点击行为、禁用态、事件 emit 不变。

兼容性边界：

- 不改变事件卡片 DOM 层级。
- 不改变 `dedupe_key` badge 预览。
- 不改变 Panel 的路由聚焦逻辑。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe focus button full tooltip：`2 passed`
- Governance timeline dedupe focus button full tooltip regression：`2 passed, 47 passed`

### F-47：Governance Timeline Dedupe Copy Button Full Tooltip

本轮继续补齐事件卡片操作区的完整 `dedupe_key` 上下文。F-46 已覆盖 `聚焦幂等键` / `已聚焦幂等键`，F-47 进一步让 `复制幂等键` / `已复制幂等键` 按钮通过 `title` 和 `aria-label` 暴露完整 key，避免维护者在只看操作按钮时无法确认复制目标。

调整：

- `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelineEventCard.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `复制幂等键` 按钮新增：
  - `title="<dedupe_key>"`
  - `aria-label="复制幂等键 <dedupe_key>"`
- `已复制幂等键` 状态新增：
  - `title="<dedupe_key>"`
  - `aria-label="已复制幂等键 <dedupe_key>"`
- 点击复制行为和复制态计时不变。

兼容性边界：

- 不改变 payload 展开、复制 Payload、复制 Snapshot 行为。
- 不改变 `聚焦幂等键` 行为。
- 不改变 Panel 的 active dedupe key 状态。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe copy button full tooltip：`2 passed`
- Governance timeline dedupe copy button full tooltip regression：`2 passed, 47 passed`

### F-48：Governance Timeline Active Dedupe Summary Button Full Tooltip

本轮把完整 `activeDedupeKey` 上下文补齐到顶部 `幂等键聚焦` summary 的操作按钮。F-45 已覆盖 summary 预览文本，F-48 进一步覆盖 `复制当前幂等键` / `已复制当前幂等键` / `清除幂等键`，让维护者在 summary 操作区也能确认按钮作用目标。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `复制当前幂等键` 按钮新增：
  - `title="<activeDedupeKey>"`
  - `aria-label="复制当前幂等键 <activeDedupeKey>"`
- `已复制当前幂等键` 状态新增：
  - `title="<activeDedupeKey>"`
  - `aria-label="已复制当前幂等键 <activeDedupeKey>"`
- `清除幂等键` 按钮新增：
  - `title="<activeDedupeKey>"`
  - `aria-label="清除幂等键 <activeDedupeKey>"`

兼容性边界：

- 不改变 summary copy / clear 行为。
- 不改变 `activeDedupeKey` 路由同步。
- 不改变事件卡片级 copy / focus 行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "copies active route-driven dedupe key"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline active dedupe summary button full tooltip：`1 passed`
- Governance timeline active dedupe summary button full tooltip regression：`2 passed, 47 passed`

### F-49：Governance Timeline Empty Dedupe Focus Clear Full Tooltip

本轮补齐 `governance_dedupe_key` 空状态的清除动作上下文。当复制链接过期或当前会话没有匹配事件时，空状态会展示 `清除幂等键聚焦`。F-49 让该按钮也通过 `title` 和 `aria-label` 暴露完整 active key，避免 stale link 场景下无法确认正在清除哪个幂等签名。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 空状态 `清除幂等键聚焦` 按钮新增：
  - `title="<activeDedupeKey>"`
  - `aria-label="清除幂等键聚焦 <activeDedupeKey>"`
- 清除后仍移除 `governance_dedupe_key` 并保留其他过滤条件。
- 空状态说明文本和完整 key 展示不变。

兼容性边界：

- 不改变正常列表态。
- 不改变 summary 区 copy / clear 按钮。
- 不改变路由过滤和事件卡片行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "explains empty route-driven dedupe key"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline empty dedupe focus clear full tooltip：`1 passed`
- Governance timeline empty dedupe focus clear full tooltip regression：`2 passed, 47 passed`

### F-50：Governance Timeline Empty Dedupe Key Full Tooltip

本轮继续完善 `governance_dedupe_key` 空状态。此前空状态已经直接展示 active key，并在清除按钮上暴露完整 key；F-50 为 key 文本本身增加稳定 class 和 `title` / `aria-label`，方便自动化测试、辅助技术以及后续治理台对空状态 key 节点做精确定位。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 空状态 key 文本新增 `.timeline-empty-dedupe-key`。
- 该节点新增：
  - `title="<activeDedupeKey>"`
  - `aria-label="当前幂等键 <activeDedupeKey>"`
- 展示文本仍为完整 active key。
- 清除按钮行为不变。

兼容性边界：

- 不改变正常列表态。
- 不改变 summary 区或事件卡片的幂等键展示。
- 不改变路由过滤和复制行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "explains empty route-driven dedupe key"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline empty dedupe key full tooltip：`1 passed`
- Governance timeline empty dedupe key full tooltip regression：`2 passed, 47 passed`

### F-51：Governance Timeline Dedupe Match Count Accessibility

本轮把 `幂等键聚焦` summary 中的匹配数从普通 muted 文本升级为稳定可观测节点。`匹配事件 N / M` 是判断当前 active key 在过滤范围内命中规模的核心信号，F-51 为该文本增加 class 和 `aria-label`，方便自动化测试、辅助技术和后续治理台精确读取。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 匹配数文本新增 `.dedupe-focus-match-count`。
- 该节点新增：
  - `aria-label="幂等键匹配事件 N / M"`
- 显示文本仍为 `匹配事件 N / M`。
- 匹配数计算仍复用 `filteredTimeline / dedupeCandidateTimeline`。

兼容性边界：

- 不改变 dedupe key 过滤。
- 不改变复制当前视图中的匹配数文本。
- 不改变 summary copy / clear 按钮。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven dedupe key filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline dedupe match count accessibility：`1 passed`
- Governance timeline dedupe match count accessibility regression：`2 passed, 47 passed`

### F-52：Governance Timeline Framework Adapter Error Type Clear Tooltip

本轮把 Framework Adapter 错误类型 summary 的清除动作补齐可访问上下文。`清除错误类型` 按钮此前只有短文案，维护者在多过滤条件叠加时需要额外从 summary 文本推断清除目标。F-52 为按钮增加 raw error type 的 `title` 和包含展示标签的 `aria-label`。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `清除错误类型` 按钮新增：
  - `title="<activeFrameworkAdapterErrorType>"`
  - `aria-label="清除错误类型 <activeFrameworkAdapterErrorTypeLabel>"`
- 点击后仍只移除 `governance_error_type`，保留 domain / severity / dedupe key 等其他过滤条件。
- 错误类型展示文本和复制当前视图内容不变。

兼容性边界：

- 不改变 Framework Adapter error type 过滤计算。
- 不改变 dedupe key 聚焦。
- 不改变事件卡片行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven framework adapter error type filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline framework adapter error type clear tooltip：`1 passed`
- Governance timeline framework adapter error type clear tooltip regression：`2 passed, 47 passed`

### F-53：Governance Timeline Framework Adapter Error Type Label Accessibility

本轮继续补齐 Framework Adapter 错误类型 summary 的可观测性。F-52 已让 `清除错误类型` 按钮携带完整上下文，F-53 进一步让错误类型展示值本身成为稳定可定位节点，便于自动化测试、辅助技术和后续治理台读取当前 error type 聚焦状态。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- 错误类型展示值新增 `.framework-error-type-focus-label`。
- 该节点新增：
  - `title="<activeFrameworkAdapterErrorType>"`
  - `aria-label="错误类型 <activeFrameworkAdapterErrorTypeLabel>"`
- 展示文本仍为 `activeFrameworkAdapterErrorTypeLabel`。
- 错误类型过滤和清除行为不变。

兼容性边界：

- 不改变 `governance_error_type` 路由参数。
- 不改变复制当前视图内容。
- 不改变 dedupe key 聚焦和事件卡片行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven framework adapter error type filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline framework adapter error type label accessibility：`1 passed`
- Governance timeline framework adapter error type label accessibility regression：`2 passed, 47 passed`

### F-54：Governance Timeline Severity Focus Label Accessibility

本轮把 `风险模式` summary 的展示值补成稳定可观测节点。路由驱动的 `governance_severity=warning` 会改变统一事件流范围，F-54 让当前 severity 状态通过 class、`title` 和 `aria-label` 暴露，方便测试、辅助技术和后续治理台读取当前风险过滤模式。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `风险模式` 展示值新增 `.severity-focus-label`。
- 该节点新增：
  - `title="<activeSeverity>"`
  - `aria-label="风险模式 <activeSeverityLabel>"`
- 展示文本仍为 `activeSeverityLabel`。
- severity 过滤行为不变。

兼容性边界：

- 不改变 `governance_severity` 路由参数。
- 不改变自动聚焦逻辑。
- 不改变 dedupe key / error type 聚焦。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven warning scope"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline severity focus label accessibility：`1 passed`
- Governance timeline severity focus label accessibility regression：`2 passed, 47 passed`

### F-55：Governance Timeline Filter Focus Label Accessibility

本轮把 `当前筛选` summary 的展示值补成稳定可观测节点。`governance_filter` 决定统一事件流的治理 domain 范围，F-55 让当前 domain 过滤状态通过 class、`title` 和 `aria-label` 暴露，和 F-54 的 severity 状态保持一致。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `当前筛选` 展示值新增 `.filter-focus-label`。
- 该节点新增：
  - `title="<activeFilter>"`
  - `aria-label="当前筛选 <activeFilterLabel>"`
- 展示文本仍为 `activeFilterLabel`。
- domain 过滤行为不变。

兼容性边界：

- 不改变 `governance_filter` 路由参数。
- 不改变 severity / error type / dedupe key 聚焦。
- 不改变复制当前视图内容。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "supports route-driven framework adapter error type filtering"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline filter focus label accessibility：`1 passed`
- Governance timeline filter focus label accessibility regression：`2 passed, 47 passed`

### F-56：Governance Timeline Plan and Step Summary Accessibility

本轮把顶部基础 summary 中的 `当前计划` 与 `聚焦步骤` 展示值补成稳定可观测节点。它们是治理时间线的上下文锚点，F-56 为两者增加 class、`title` 和 `aria-label`，方便自动化测试、辅助技术和后续治理台精确读取当前计划目标与聚焦步骤。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `当前计划` 展示值新增 `.plan-objective-label`。
- `聚焦步骤` 展示值新增 `.focus-step-label`。
- 两个节点都新增：
  - `title="<当前展示值>"`
  - `aria-label="<summary label> <当前展示值>"`
- 展示文本仍沿用原有 fallback：无值时为 `-`。

兼容性边界：

- 不改变 `focusItem` 选择逻辑。
- 不改变计划、审批、run、trace 统计。
- 不改变过滤、复制和事件卡片行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "shows phase a run"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline plan and step summary accessibility：`1 passed`
- Governance timeline plan and step summary accessibility regression：`2 passed, 47 passed`

### F-57：Governance Timeline Audit and Trace Count Accessibility

本轮把顶部基础 summary 中的 `审计事件` 与 `运行 Trace` 计数补成稳定可观测节点。两者是判断当前聚焦步骤治理密度的核心数字，F-57 为计数值增加 class、`title` 和 `aria-label`，方便自动化测试、辅助技术和后续治理台读取。

调整：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
- `docs/roadmap/next_phase_hardening.md`

行为边界：

- `审计事件` 计数新增 `.audit-count-label`。
- `运行 Trace` 计数新增 `.trace-count-label`。
- 两个节点都新增：
  - `title="<count>"`
  - `aria-label="<summary label> <count>"`
- 计数仍分别来自 `focusItem.audit_trail.length` 和 `focusItem.run_trace.length`。

兼容性边界：

- 不改变审计和 trace 计数逻辑。
- 不改变统一事件流构造。
- 不改变过滤、复制和事件卡片行为。

已执行：

```powershell
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js -t "shows phase a run"
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelineEventCard.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- Governance timeline audit and trace count accessibility：`1 passed`
- Governance timeline audit and trace count accessibility regression：`2 passed, 47 passed`

### F-58：Runtime Contract Summary Artifact Hardening

本轮把 `runtime_contract_gate.runtime_contract_summary` 的读取边界再收紧一层。`runtime_contract_summary` 和 `contract_checks` 都来自质量门禁 JSON artifact，虽然正常情况下由 `quality_gate_report.py` 生成，但企业化治理链路里仍要允许旧报告、手工报告或异常输出存在脏字段。现在上游报告脚本和后端 profile 读取都会 fail-closed 处理计数字段，Markdown summary 表格也会转义自由文本，而不是让 quality gate artifact 生成、Runtime Profile 读取或审计摘要渲染被脏字段破坏。

调整：

- `backend/services/runtime_contract_gate_service.py`
- `tests/agent_framework/test_runtime_contract_gate_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`

行为边界：

- `runtime_contract_summary.check_count / failed_check_count / missing_payload_count` 会按非负整数归一化。
- `quality_gate_report.py` 生成 `runtime_contract_summary` 时，`embedded_sdk_event_payloads.missing_payload_count` 不可解析或为负数会按 `0` 处理。
- `quality_gate_report.py` 抽取和渲染 `contract_checks` 时会忽略非对象 check；原始 `structured_output` 仍保留完整 smoke JSON，便于排障。
- `quality_gate_report.py` 渲染 Markdown summary 时会忽略非对象 `runtime_contract_summary`，避免旧报告或手工报告破坏摘要渲染。
- `quality_gate_report.py` 渲染 Markdown summary 时会忽略非对象 step，避免旧报告或手工报告破坏主表、失败列表和 runtime contract 表格。
- `quality_gate_report.py` 渲染 Markdown summary 时会把非 list 的 `steps / failed_steps` 按空列表处理，避免旧报告或手工报告顶层类型漂移导致 TypeError。
- Runtime Contract Gate 读取质量门禁 artifact 时会把非 list 的 `steps / contract_checks` 按空列表处理，避免脏 artifact 让 Runtime Profile 读取链路 500。
- `quality_gate_report.py` 与 Runtime Contract Gate 读取 `observed_status_kinds` 时只接受 list；字符串、数字等非 list 值会按空列表处理，避免误拆字符串或中断 Runtime Profile 读取。
- `quality_gate_report.py` 渲染 Runtime Contract Summary 表格时会把非 object 的 `approval_replay_coverage` 按缺失处理，coverage 显示为 `no`，避免旧报告或手工报告破坏 Markdown summary。
- `approval_replay_coverage.event_payload_sample` 会按 fail-closed 布尔语义读取；字符串 `"false"` 不再因为 truthiness 被误判为覆盖。
- `quality_gate_report.py` 渲染 object step 时会容忍 `name / passed / exit_code / duration_seconds` 缺失，避免字段裁剪后的旧报告破坏 Markdown summary。
- `quality_gate_report.py` 渲染顶层报告字段时会容忍 `passed / step_count / failed_steps / steps` 缺失，避免旧报告或手工报告无法生成 Markdown summary。
- `quality_gate_report.py` 渲染旧报告或手工报告时，如果顶层 `failed_steps` 缺失，会从有效 steps 中 `passed = false` 的项推导失败列表，避免摘要失败数与主表冲突。
- `quality_gate_report.py` 渲染 `passed` 状态时会 fail-closed 归一化，避免字符串 `"false"` 被 Python truthiness 误渲染为 PASS。
- 如果 report summary 中的计数字段不可解析或为负数，使用 `contract_checks` 推导值。
- `contract_checks[*].missing_payload_count / checked_event_count` 也会按非负整数归一化；不可解析或为负数时返回 `None`，summary fallback 按 `0` 处理。
- `quality_gate_report.py` 渲染 Markdown 表格时会转义 `|` 并折叠换行，避免 step/check/failure reason 或 summary 字段破坏表格列结构。
- 一旦计数字段发生回退，`runtime_contract_summary.overall_status` 也跟随 `contract_checks` 推导结果，避免出现 `runtime_contract_gate.overall_status = degraded` 但 summary 仍显示 `healthy` 的矛盾状态。
- 正常 report summary 不受影响，仍保留 `approval_replay_coverage.observed_status_kinds` 这类 richer artifact 信息。

兼容性边界：

- 不改变 `quality_gate_report.py` 的输出结构。
- 不新增 API 字段，不改变 Runtime Surface 前端消费路径。
- 只加强 artifact 读取容错；报告缺失或 `contract_checks` 缺失时仍保持 `unknown` 语义。

已执行：

```powershell
conda run -n myenv python -m unittest tests.agent_framework.test_runtime_contract_gate_service.RuntimeContractGateServiceTests.test_build_runtime_contract_falls_back_when_summary_counts_are_invalid -v
conda run -n myenv python -m unittest tests.agent_framework.test_runtime_contract_gate_service.RuntimeContractGateServiceTests.test_build_runtime_contract_ignores_invalid_check_payload_counts -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_run_step_ignores_invalid_runtime_contract_payload_count -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_escapes_runtime_contract_check_table_cells -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_escapes_runtime_contract_summary_table_cells -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_run_step_ignores_non_object_runtime_contract_checks -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_ignores_non_object_runtime_contract_checks -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_ignores_non_object_runtime_contract_summary -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_ignores_non_object_steps -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_ignores_non_list_steps_fields -v
conda run -n myenv python -m unittest tests.agent_framework.test_runtime_contract_gate_service.RuntimeContractGateServiceTests.test_build_runtime_contract_ignores_non_list_steps_and_contract_checks -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_run_step_ignores_non_list_observed_status_kinds tests.agent_framework.test_runtime_contract_gate_service.RuntimeContractGateServiceTests.test_build_runtime_contract_ignores_non_list_observed_status_kinds -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_treats_non_object_approval_replay_coverage_as_missing -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_treats_string_false_approval_replay_coverage_as_missing tests.agent_framework.test_runtime_contract_gate_service.RuntimeContractGateServiceTests.test_build_runtime_contract_treats_string_false_approval_replay_coverage_as_missing -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_handles_step_objects_with_missing_fields -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_handles_missing_top_level_fields -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_derives_failed_steps_when_missing -v
conda run -n myenv python -m unittest tests.agent_framework.test_quality_gate_report.QualityGateReportTests.test_render_summary_treats_string_false_status_as_fail -v
```

结果：

- Runtime contract summary artifact hardening：`1 passed`
- Runtime contract check payload count hardening：`1 passed`
- Quality gate report runtime contract payload count hardening：`1 passed`
- Quality gate report markdown table hardening：`1 passed`
- Quality gate report runtime contract summary markdown hardening：`1 passed`
- Quality gate report non-object contract check hardening：`1 passed`
- Quality gate report non-object contract check markdown hardening：`1 passed`
- Quality gate report non-object runtime contract summary hardening：`1 passed`
- Quality gate report non-object step markdown hardening：`1 passed`
- Quality gate report non-list step field markdown hardening：`1 passed`
- Runtime contract gate non-list artifact field hardening：`1 passed`
- Runtime contract observed status kinds list hardening：`2 passed`
- Quality gate report approval coverage markdown hardening：`1 passed`
- Runtime contract approval coverage boolean hardening：`2 passed`
- Quality gate report missing step field markdown hardening：`1 passed`
- Quality gate report missing top-level field markdown hardening：`1 passed`
- Quality gate report derived failed steps markdown hardening：`1 passed`
- Quality gate report passed flag normalization：`1 passed`
