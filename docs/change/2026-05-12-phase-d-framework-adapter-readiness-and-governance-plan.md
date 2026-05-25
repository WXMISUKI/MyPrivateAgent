# Phase D Framework Adapter Readiness And Governance Plan

> 目标读者：继续完善 `MyPrivateAgent` 通用智能体底座的开发者、评审者、未来外部 framework adapter 接入方。

## 1. 阶段定位

Phase C 已经把 framework adapter 的平台边界硬化完成：

- 有稳定的 SPI 与 registry
- 有 `LocalFakeFrameworkAdapter` pilot
- 有 trace / audit / snapshot / smoke / CI 门禁

Phase D 的重点不再是继续强化 contract 本身，而是把“外部 framework adapter 的接入前准备”做成一条可治理、可诊断、可预检、可在前端操作的 readiness 链路。

本阶段默认以 `LangGraphDraftAdapter` 作为真实外部框架候选，但仍然坚持两个边界：

1. 先做接入前治理，不直接把真实外部执行塞进主链路。
2. 先区分“已注册”和“可执行”，不让占位 adapter 被误判成运行时能力。

## 2. 当前目标

Phase D 当前已经完成的，不是 LangGraph 真执行接入，而是以下平台能力：

- 外部 adapter 的受控注册
- readiness contract 与执行阻断语义
- doctor / health / runtime profile 一致诊断
- precheck 独立入口
- external pilot 独立入口
- remediation actions 治理建议
- Runtime Surface / Governance Timeline 的前端闭环展示

换句话说，当前平台已经能回答这些问题：

- 哪些 framework adapter 已注册？
- 哪些 adapter 只是占位、哪些已经 ready？
- 当前阻塞点是缺包、缺环境变量，还是 runtime 开关未启？
- 如何在不触发真实执行的前提下做预检？
- 如何在受控开关下触发一次最小真实 external pilot？
- 如何把诊断结果和修复建议沉淀进治理时间线？

## 3. Phase D-0：Draft Adapter 占位注册

### 实施状态（2026-05-12）

- 已新增环境变量开关：
  - `ENABLE_LANGGRAPH_DRAFT_ADAPTER`
- 已新增 `LangGraphDraftAdapter` 的 draft 注册位：
  - `adapter_id = langgraph_draft`
  - `framework_name = LangGraph`
- 当开关打开时，adapter 会注册进 framework adapter registry，并进入 `adapter_health`。
- 当前 draft adapter 默认不进入真实执行链，只作为 readiness 与治理占位骨架。

### 当前价值

- registry、health、runtime surface 可以先承载真实外部 framework 的“存在性”。
- 后续切换到真实执行实现时，不需要重新设计治理边界。

## 4. Phase D-1 ~ D-3：Readiness Contract 与执行边界

### 当前实现

后端 `FrameworkAdapterHealth` 已补齐以下关键字段：

- `package_installed`
- `runtime_enabled`
- `execution_mode`
- `required_env`
- `missing_env`
- `required_packages`
- `missing_packages`
- `configuration_status`
- `execution_block_reason`

平台语义已经明确区分：

- `adapter 已注册`
- `adapter 可观察`
- `adapter 可预检`
- `adapter 可执行`

其中 `AgentFrameworkAdapter.can_execute()` 已作为统一执行闸门；`FrameworkAdapterRuntimeService` 对不可执行 adapter 会直接拒绝，不再误进 pilot 或运行链路。

### `LangGraphDraftAdapter` 当前 readiness 规则

按以下顺序判定：

1. 缺包：
   - `configuration_status = missing_package`
2. 包已安装但缺环境变量：
   - `configuration_status = missing_env`
3. 包和环境变量已齐，但 runtime 开关未启：
   - `configuration_status = runtime_disabled`
4. 全部满足：
   - `configuration_status = ready`

### 当前保留边界

- `ENABLE_LANGGRAPH_RUNTIME_EXECUTION=true` 现在是 readiness 前置条件之一，不单独代表“允许真实 external pilot”。
- `ENABLE_LANGGRAPH_EXTERNAL_PILOT=true` 才代表允许发起受控真实 external pilot。
- 当前未把外部 framework 接进 chat 主执行路径。
- 当前不处理 LangGraph graph schema、node runtime、checkpointing、external worker lifecycle。

## 5. Phase D-4：Doctor / Health / Runtime Diagnostics 收口

### 当前实现

`StartupDiagnosticsService` 已增加 `framework_adapters` 检查项，并统一复用 `ToolRuntimeService.build_adapter_health_contract()`。

规则如下：

- `overall_status = healthy` -> `ok`
- `overall_status = not_configured` -> `warn`
- `overall_status = degraded` -> `fail`

诊断出口已经贯通到：

- `GET /api/health`
- `GET /api/doctor`
- `python backend/scripts/doctor.py`

### 当前可输出内容

每个 adapter 当前都会输出：

- `status`
- `configuration_status`
- `execution_mode`
- `missing_packages`
- `missing_env`
- `execution_block_reason`

这意味着 draft adapter 的阻塞原因不再只存在于面板展示，而是进入了后端标准诊断口径。

## 6. Phase D-5：Remediation Actions 与治理建议

### 当前实现

`framework_adapters` 诊断块已支持输出 `remediation_actions`，当前至少包括三类：

- `install_package`
- `configure_env`
- `enable_runtime_execution`

每条 remediation action 当前会带：

- `adapter_id`
- `framework_name`
- `type`
- `severity`
- `message`
- `next_steps`

### 时间线沉淀

`doctor_run_completed` 的 timeline payload 已写入：

- `framework_adapters.status`
- `framework_adapters.details`
- `framework_adapters.remediation_actions`

这意味着治理时间线可以同时承载：

- readiness 结论
- 阻塞原因
- 修复建议

而不只是知道 doctor 执行过一次。

## 7. Phase D-6：最小真实环境检测

### 当前实现

`LangGraphDraftAdapter.health_check()` 已不再固定把 `langgraph` 判为缺失，而是通过标准库能力做本机最小检测：

- `importlib.util.find_spec("langgraph")`

### 当前价值

- 如果本机已安装 `langgraph`，状态会自动从 `missing_package` 进入下一层判断。
- 平台对外部 adapter 的诊断，不再完全依赖静态占位逻辑。

### 当前保留边界

- 当前只做 Python 包存在性检测，不做版本约束与兼容矩阵校验。
- 当前不验证 LangGraph 相关 import 细项是否可正常执行具体 graph runtime。

## 8. Phase D-7：Precheck 独立入口与治理闭环

### 当前实现

后端已新增独立预检入口：

- `POST /api/runtime-framework-adapters/precheck`

由 `FrameworkAdapterRuntimeService.precheck_adapter(...)` 统一返回：

- `ready`
- `status`
- `configuration_status`
- `execution_mode`
- `package_installed`
- `runtime_enabled`
- `required_packages / missing_packages`
- `required_env / missing_env`
- `execution_block_reason`
- `detail`

### 时间线接入

当带有会话上下文时，预检结果会进入治理链路：

- trace event: `framework_adapter_precheck_completed`
- audit event: `framework_adapter_precheck_completed`
- snapshot: `snapshot_ref`

### 与 pilot 的职责分离

- `local_fake_framework`
  - 继续负责 `pilot-run`
  - 验证 `translate_input -> stream_events -> translate_output -> trace/audit`
- `langgraph_draft`
  - 负责 `precheck`
  - 验证 readiness，不进入真实执行链

这一步把“执行闭环验证”和“外部框架接入前诊断”明确拆开了。

## 9. Phase D-8：受控 External Pilot 骨架

### 当前实现

后端已新增受控真实 external pilot 入口：

- `POST /api/runtime-framework-adapters/external-pilot`

该入口当前只接受：

- `adapter_id = langgraph_draft`

并且要求同时满足：

- `configuration_status = ready`
- `ENABLE_LANGGRAPH_RUNTIME_EXECUTION = true`
- `ENABLE_LANGGRAPH_EXTERNAL_PILOT = true`

### 当前执行骨架

当前最小真实执行链已经接通：

- `LangGraphRequestTranslator`
- `LangGraphRuntimeClient`
- `LangGraphEventTranslator`
- `LangGraphOutputTranslator`

当前 external pilot 在真正发起流式请求前，还会执行最小 preflight：

- `assistant_id` 非空且满足最小 identity 约束
- `endpoint` 必须是合法 `http/https` URL
- transport 必须先通过一次 reachability probe
- probe 必须返回 assistant identity evidence，当前支持三种最小证据形状：
  - `assistant_exists = true`
  - `assistant_id` 与请求值精确匹配
  - `assistants[]` 包含当前请求的 assistant identity

preflight 失败时，当前会稳定归类为：

- `configuration_error`
- `connectivity_error`
- `protocol_error`

其中：

- `protocol_error`
  - probe 没有返回 assistant identity evidence
  - 或 probe 返回了不受支持的 evidence 形状
- `configuration_error`
  - upstream 明确表示当前 assistant identity 不存在
  - 或 probe 回传的 assistant identity 与请求值不一致

平台已能把真实 external pilot 结果继续沉淀进治理链路：

- trace event: `framework_adapter_external_pilot_completed`
- trace event: `framework_adapter_external_error`
- audit event: `framework_adapter_external_pilot_completed`
- snapshot: `snapshot_ref`
- `GET /api/health`、`GET /api/doctor` 与 `python backend/scripts/doctor.py`
  - `checks.framework_adapters.latest_external_pilot_failure`
  - `checks.framework_adapters.external_pilot_failure_counts`
  - 可汇总最近一次 external pilot 失败分类、adapter 身份、错误详情与 snapshot 引用
  - 可额外输出最近一段时间的 external pilot 失败总数与 `error_type` 分布

### 当前价值

- 平台已经不只会 `precheck`，也能在严格开关下完成一次最小真实外部调用闭环。
- 本地 fake pilot、readiness precheck、真实 external pilot 三类能力已经明确分层，不再混用。
- 真实 external 调用失败时，不会退化成模糊报错，而是进入统一治理语义。

### 当前保留边界

- 当前 external pilot 仍是单 adapter、单请求、单次受控执行。
- 当前不接入 chat 主执行路径。
- 当前 transport 仍以最小骨架为主，不处理多会话池、长生命周期 worker、checkpoint 管理。
- 当前 reachability probe 只验证“目标可达与协议形状”，不等价于完整上游业务健康检查。

## 10. 前端治理面完成面

### Runtime Surface

`RuntimeSurfacePanel` 当前已经具备：

- `adapter_health` 的扩展字段展示
- `local_fake_framework` 的 `运行 Pilot`
- `langgraph_draft` 的 `运行预检`
- `langgraph_draft` 的 `运行 External Pilot`
- 最近一次 `Pilot / Precheck / External Pilot` 结果卡
- 最近一次 `External Pilot 失败` 诊断摘要卡
- `External Pilot 失败` 摘要卡支持展示失败总数、统计窗口、样本数与 `error_type` 分布
- `External Pilot 失败` 摘要卡支持按 `error_type` 直接跳转治理时间线
- `External Pilot 失败` 错误分布按钮支持根据当前 `governance_error_type` 路由显示激活态
- `snapshot_id`
- `复制快照命令`
- `查看时间线`
- 受控修复命令草案复制

此外，前端已完成一轮治理口径收口：

- `configuration_status`
  - 例如 `缺包`
- `execution_mode`
  - 例如 `外部草稿运行时`
- `pkg / runtime / 依赖包 / 环境变量 / 阻塞原因`
  - 已有中文摘要 + 原始枚举或原始原因

### Governance Timeline

`GovernanceTimelinePanel` 当前已经具备：

- `framework_adapter_precheck_completed` 事件识别
- `framework_adapter_external_pilot_completed` 事件识别
- `framework_adapter_external_error` 事件识别
- 基于 `doctor_run_completed.payload.framework_adapters.latest_external_pilot_failure` 注入 synthetic diagnostic entry
- `LocalFakeFramework Pilot`
- `LangGraph Precheck`
- `LangGraph External Pilot`
- `LangGraph External Pilot 失败诊断`
- `LangGraph 修复建议`
- remediation actions 摘要卡
- 快照聚焦
- `External Pilot 失败诊断` 摘要卡支持展示失败总数、统计窗口、样本数与 `error_type` 分布
- `External Pilot 失败诊断` 摘要卡支持 `打开运行时面板`
- `External Pilot 失败诊断` 摘要卡支持 `复制快照命令`
- `Governance Timeline` 支持 `governance_error_type` 路由过滤
- `Governance Timeline` 支持直接清除 `error_type` 过滤且保留当前域与告警范围
- `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 已形成 `governance_error_type` 双向一致：
  - 时间线过滤到某个错误类型后，运行时面板对应错误分布按钮会高亮
  - 运行时面板点击错误分布按钮后，会进入同一个时间线过滤态
- `打开运行时面板`
- `复制修复命令`

当前 `framework_adapter` 治理视角已经能覆盖：

- pilot
- precheck
- external pilot
- remediation

四类信息，并能彼此跳转。

## 11. 当前验证基线

当前 Phase D 涉及的轻量回归主要落在以下测试：

后端：

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_framework_adapter_runtime_service tests.agent_framework.test_framework_adapter_runtime_service_external_pilot tests.agent_framework.test_startup_diagnostics_service tests.agent_framework.test_health_router tests.agent_framework.test_doctor_script -v
```

前端：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

这些回归当前覆盖的核心面包括：

- draft adapter 注册与 readiness contract
- precheck API 与 timeline 记录
- external pilot API 与 timeline 记录
- external pilot preflight 的 `assistant_id / endpoint / probe` 失败分支
- doctor / health / remediation_actions
- Runtime Surface 的 pilot / precheck / external pilot 操作闭环
- Governance Timeline 的 pilot / precheck / external pilot / remediation 摘要卡与命令动作

## 11.1 统计窗口收口（2026-05-13）

`external_pilot_failure_counts` 已从粗略统计升级为带边界的 contract：

```json
{
  "total": 3,
  "window_scope": "recent_plan_items",
  "sample_size": 50,
  "by_error_type": {
    "protocol_error": 2,
    "connectivity_error": 1
  }
}
```

当前语义固定为：

- `window_scope = recent_plan_items`：统计范围是最近 PlanItem 的 trace，不表示全量历史。
- `sample_size = 50`：最多抽取最近 50 个 PlanItem，并对每个 PlanItem 查最近 50 条 external error trace。
- `total`：当前窗口内命中的 external pilot error 事件总数。
- `by_error_type`：当前窗口内按 `error_type` 聚合的数量。

RuntimeSurfacePanel 与 GovernanceTimelinePanel 均已展示 `统计窗口 / 样本数`，避免用户误解错误分布口径。

本轮验证：

```powershell
C:\Users\dddsg\miniconda3\python.exe -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_doctor_script -v
```

结果：`Ran 25 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：`2 passed, 60 passed`

## 12. 当前阶段结论

Phase D 当前已经完成的，不是“接好了 LangGraph”，而是“把真实外部 framework 接入前必须稳定的治理面”基本铺平了：

- 有 draft adapter 占位
- 有 readiness contract
- 有 precheck 入口
- 有受控 external pilot 入口
- 有 doctor / health / timeline 诊断
- 有 remediation actions
- 有 Runtime Surface / Governance Timeline 双侧前端闭环

如果现在直接切真实外部执行，平台已经具备：

- 注册位
- 诊断位
- 治理位
- 快照位
- 预检位
- 最小真实执行位

缺的已经不是“有没有执行骨架”，而是更深一层的生产级外部执行约束与运行时治理细节。

## 13. 下一步建议

下一步不建议再把重点放在“有没有 external pilot 骨架”，因为这一层已经落地。更合理的是继续收紧 D-9 的工程边界：

1. 收紧真实 external pilot 的 transport / config 约束
   - 包版本约束
   - graph identity 校验
2. 继续深化 external pilot 的失败分类与手工验收
   - 确保 `connectivity / authentication / protocol / upstream` 语义稳定
3. 再决定是否把真实外部 framework 接进更深一层的受控 pilot
   - 仍不建议直接接入 chat 主路径

更具体的 D-8 / D-9 设计边界与最小执行骨架，已转入：

- [2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md](D:\AI\AIcode\MyPrivateAgent\docs\change\2026-05-12-phase-d8-d9-external-framework-adapter-execution-skeleton.md)
