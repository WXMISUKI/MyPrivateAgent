# Phase C Runtime Contract Hardening Plan

> 目标读者：继续完善 `MyPrivateAgent` 通用智能体底座的开发者、评审者、未来 adapter/SDK 接入方。

## 1. 阶段目标

Phase B 已经把能力层主干收口到稳定 contract：

- `tool_runtime`
- `mcp_runtime`
- `skill_contract`
- `memory_contract`
- `command_contract`
- `adapter_health`

Phase C 的重点不是继续横向堆功能，而是把这些 contract 硬化成可长期演进的平台边界。后续无论接 LangGraph、DeepAgents-style、CrewAI-style、自研 adapter，还是暴露 Embedded SDK，都不能绕过这些稳定边界。

## 2. Phase C-1：Contract Snapshot Guard

### 目标

给 Runtime Surface 增加版本化 contract snapshot，让后续变更可以快速判断：

- 哪些 contract 是平台稳定边界。
- 当前 contract 是否缺失。
- 稳定字段是否被破坏。
- 本次运行时能力面是否整体健康。

### 实施状态（2026-05-11）

- 已新增 `RuntimeContractSnapshotService`。
- 已新增 `phase-c-runtime-contract-snapshot-v1`。
- 已锁定 6 个核心 contract 的稳定字段：
  - `tool_runtime`
  - `mcp_runtime`
  - `skill_contract`
  - `memory_contract`
  - `command_contract`
  - `adapter_health`
- 已支持按 contract 输出：
  - `contract_name`
  - `version`
  - `status`
  - `stable_fields`
  - `missing_fields`
  - `field_count`
  - `fingerprint`
- 已支持整体输出：
  - `overall_status`
  - `contract_count`
  - `missing_contract_count`
  - `missing_field_count`
  - `fingerprint`
- `RuntimeSurfaceService.get_runtime_profile()` 已暴露 `contract_snapshot`。
- 前端 `RuntimeSurfacePanel` 已新增 `Contract Snapshot` 卡片，用于查看缺失 contract、缺失字段、整体 fingerprint 和每个 contract 的状态。

### 当前保留边界

- Snapshot 当前检查的是稳定字段存在性和结构形状，不对每个字段的业务取值做强校验。
- Fingerprint 用于快速发现 contract 形状变化，不用于安全签名。
- 本轮不阻断运行时，只暴露 `healthy / degraded`。后续可在 CI 或质量门禁中把 degraded 升级为失败。

### 验证记录

```powershell
python -m unittest tests.agent_framework.test_runtime_contract_snapshot_service tests.agent_framework.test_runtime_surface_service -v
```

结果：`Ran 4 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`1 passed, 10 passed`

## 3. Phase C-2：Adapter Pilot 全链路

### 建议目标

选择一个低风险 adapter pilot，不直接上复杂外部依赖，先验证完整平台链路：

```text
translate_input
  -> stream_events
  -> translate_output
  -> AgentEvent
  -> runtime trace / audit
  -> RuntimeSurface / Governance Console
```

### 推荐选择

优先做 `LocalFakeFrameworkAdapter`，而不是马上接 LangGraph / DeepAgents / CrewAI。

原因：

- 不引入外部依赖，测试稳定。
- 能验证平台 SPI 是否足够清晰。
- 能先打通事件、审批、审计、trace 的平台链路。
- 后续真实框架 adapter 只需要替换外部执行实现，不需要重写平台治理链路。

### 验收标准

- Adapter 输入不直接泄露业务系统内部对象。
- Adapter 输出必须统一翻译为 `AgentEvent`。
- Adapter 执行事件进入 runtime trace。
- Adapter 健康进入 `adapter_health`。
- Contract snapshot 仍保持 `healthy`。

### 当前进展（2026-05-11）

- 已新增 `LocalFakeFrameworkAdapter` 的受控注册开关：
  - 环境变量 `ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER=true` 时自动注册到 framework adapter registry。
- 已新增 `FrameworkAdapterRuntimeService`：
  - 负责执行 `translate_input -> stream_events -> translate_output`。
  - 负责把 adapter 事件统一写入 `run trace / audit`。
- 已新增受控 pilot API：
  - `POST /api/runtime-framework-adapters/pilot-run`
  - 仅在 `ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER=true` 时允许执行。
- 已为 `framework_adapter` 事件补齐统一 trace 映射：
  - `framework_adapter_status`
  - `framework_adapter_reasoning`
  - `framework_adapter_output`
- 当前 pilot 已验证“平台约束 adapter”的最小治理闭环，但尚未接入正式 chat 主执行路径。

### 本轮验证记录

```powershell
python -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_chat_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_runtime_contract_snapshot_service -v
```

结果：`Ran 58 tests ... OK`

## 4. Phase C-3：Quality Gate 与 CI 接入

### 建议目标

把 contract snapshot 从“运行时可观察”升级为“开发质量门禁”。

建议增加：

- 后端 contract snapshot 单测。
- Runtime profile schema regression 测试。
- 前端 RuntimeSurfacePanel contract 渲染测试。
- 可选 smoke 脚本：启动后端后读取 `/runtime/profile` 并检查 `contract_snapshot.overall_status`。

### 当前进展（2026-05-11）

- 已新增 `backend/scripts/runtime_contract_smoke.py`：
  - 校验 `GET /api/runtime-profile`
  - 强制检查 `contract_snapshot.overall_status == healthy`
  - 校验 `POST /api/runtime-framework-adapters/pilot-run`
  - 强制检查 local fake adapter pilot 可执行且返回最小事件流
  - 当 `contract_snapshot` degraded 或 pilot 返回不完整事件流时，脚本必须非零退出
- 已新增单测 `tests.agent_framework.test_runtime_contract_smoke`
- 已接入现有质量门禁链路：
  - `backend/scripts/quality_gate_smoke.ps1`
  - `backend/scripts/quality_gate_report.py`
- 已接入前端 smoke 链路：
  - `backend/scripts/frontend_health_alert_smoke.ps1`
  - 覆盖 `RuntimeSurfacePanel.test.js`
- `RuntimeSurfacePanel` 已增加本地 pilot 触发入口：
  - 对 `local_fake_framework` 展示 `运行 Pilot`
  - 返回最近一次 `run_id / event_count / final_output`
  - 用于直接验证 adapter pilot 的最小治理闭环

### 本轮验证记录

```powershell
python -m unittest tests.agent_framework.test_runtime_contract_smoke tests.agent_framework.test_health_router tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_runtime_contract_snapshot_service tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_spi -v
```

结果：`Ran 26 tests ... OK`

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/ChatView.test.js src/components/__tests__/SettingsView.test.js
```

结果：`3 passed, 21 passed`

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`1 passed, 12 passed`

## 5. 当前下一步

Phase C 当前已完成第一轮收口，后续外部 framework adapter 的 readiness、precheck、doctor remediation 与前端治理闭环，已转入：

- [2026-05-12-phase-d-framework-adapter-readiness-and-governance-plan.md](D:\AI\AIcode\MyPrivateAgent\docs\change\2026-05-12-phase-d-framework-adapter-readiness-and-governance-plan.md)

如果继续深化 Phase C 本身，建议仅保留两类工程化动作：

- 将 `runtime_contract_smoke.py` 持续维持在 CI 默认门禁中
- 视情况把 degraded snapshot 提升为质量门禁失败条件
