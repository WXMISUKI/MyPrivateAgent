# Phase D-8 D-9 External Framework Adapter Execution Skeleton

> 目标读者：准备把 `LangGraphDraftAdapter` 从 readiness 占位推进到真实受控执行骨架的开发者、评审者、平台治理设计者。

## 1. 文档目的

这份文档不描述“如何把 LangGraph 真正完整接入业务主链路”，而是定义一个更小、更可控的目标：

- 在不污染现有 chat 主执行路径的前提下
- 给外部 framework adapter 增加最小真实执行骨架
- 让它可以在受控 pilot 中跑通一次真实请求
- 同时不破坏 Phase C / Phase D 已经建立的治理边界

换句话说，D-8 / D-9 的核心不是“功能更强”，而是“执行实现第一次落地时，不绕过平台治理”。

## 2. 当前边界回顾

当前仓库已经具备：

- `AgentFrameworkAdapter` SPI
- `LocalFakeFrameworkAdapter` 的闭环 pilot
- `LangGraphDraftAdapter` 的 readiness contract
- `precheck` 独立入口
- doctor / health / timeline / runtime surface / remediation 完整治理链路

当前仍然缺失的是：

- 外部 framework 的真实 request 发起逻辑
- 外部 framework 返回事件到平台事件的稳定翻译层
- 真实 pilot 的受控执行器

因此 D-8 / D-9 的最小目标应限定为：

1. 只增加“受控 pilot 执行骨架”
2. 不进入 chat 主路径
3. 不引入复杂 graph authoring / workflow 编辑能力
4. 不处理多 worker、持久 checkpoint、长生命周期外部会话池

## 3. 推荐拆分

建议把 D-8 / D-9 拆成两个连续小阶段：

### Phase D-8：Execution Skeleton

目标：

- 为 `langgraph_draft` 增加最小真实执行骨架
- 让平台第一次真正对接外部 runtime client
- 但只允许走受控 pilot

### Phase D-9：Governed External Pilot

目标：

- 把真实执行骨架接进现有 pilot 治理链路
- 补齐运行期失败分类、快照、事件映射、受控门禁

这两个阶段要严格控制范围，避免一上来就做成“第二套主执行引擎”。

## 4. D-8：最小执行骨架

### 4.1 最小模块切分

建议新增四类职责，不要把所有逻辑直接堆进 `LangGraphDraftAdapter`：

1. `LangGraphRuntimeClient`
   - 负责 HTTP 或 SDK 调用外部 LangGraph runtime
   - 负责超时、错误包装、最小认证头构造

2. `LangGraphRequestTranslator`
   - 负责把平台 `messages + execution_context` 翻译成 LangGraph runtime 请求体

3. `LangGraphEventTranslator`
   - 负责把外部 runtime 返回的事件或块翻译成平台 `framework_adapter_*` 事件

4. `LangGraphOutputTranslator`
   - 负责把外部 runtime 最终输出翻译为平台 `AgentEvent(content)` 兼容形状

### 4.2 为什么必须拆分

如果把这些职责直接堆在 adapter 类里，会立刻出现三个问题：

1. readiness 逻辑和执行逻辑耦合
2. precheck 与 runtime 执行无法分别测试
3. 后续换框架时无法复用 translator / client 模式

平台已经在 Phase C / D 里把治理边界做出来了，执行实现也必须遵循同样的可替换结构。

### 4.3 推荐目录

建议放在：

- `backend/agent_framework/external/langgraph_client.py`
- `backend/agent_framework/external/langgraph_translators.py`

或等价目录；关键是不要继续把真实外部执行逻辑堆进 `framework_adapters.py`。

`framework_adapters.py` 继续作为：

- SPI 定义
- draft adapter 定义
- registry 装配点

而不承担外部 runtime client 的细节实现。

## 5. D-8：最小请求形状

### 平台输入

当前平台对 adapter 已有的最小输入是：

- `run_id`
- `messages`
- `execution_context`

建议 D-8 继续保持这个最小边界，不新增业务耦合对象。

### LangGraph draft request 建议形状

建议 translator 输出的内部请求结构先固定成：

```json
{
  "adapter_id": "langgraph_draft",
  "framework_name": "LangGraph",
  "run_id": "run_xxx",
  "assistant_id": "draft-assistant",
  "endpoint": "http://...",
  "messages": [
    {"role": "user", "content": "hello"}
  ],
  "execution_context": {
    "plan_id": 123,
    "plan_item_id": 456,
    "run_kind": "framework_adapter"
  }
}
```

这里的重点不是精确对齐某个真实 LangGraph SDK，而是先定义平台内部 translator 的稳定输出。

### 约束

- 不直接把 SQLAlchemy model 或前端 payload 透传给 client
- 不让 translator 读取数据库
- 不让 client 理解 planner / scheduler 业务语义

## 6. D-8：最小事件形状

真实外部 runtime 接入后，平台不能直接暴露外部事件原文，而应继续翻译成现有治理可识别事件。

建议最小保留三类：

1. `framework_adapter_status`
   - 例如：请求已发出、外部 runtime 已接受、流已结束

2. `framework_adapter_reasoning`
   - 可选，只有当外部 runtime 明确给出 reasoning 或 progress 时才发

3. `framework_adapter_output`
   - 最终内容输出

建议新增但仍受控的一类：

4. `framework_adapter_external_error`
   - 用于区分：
     - endpoint 不通
     - 认证失败
     - 协议不兼容
     - 外部 runtime 5xx

原因很直接：如果真实外部 runtime 接入后还只返回模糊 `ValueError`，治理面会退化。

## 7. D-8：最小错误分类

建议在真实执行骨架里先定义一层轻量错误分类，不等到后面再补。

建议至少区分：

- `configuration_error`
  - 缺 endpoint / assistant_id / runtime flag
- `connectivity_error`
  - endpoint 不可达、DNS、超时
- `authentication_error`
  - token 或授权失败
- `protocol_error`
  - 外部返回形状不符合预期
- `upstream_runtime_error`
  - 外部 framework 自身失败

这些错误最终都要能映射到：

- trace / audit payload
- `execution_block_reason` 或 `detail`
- Runtime Surface / Governance Timeline 可理解的治理语义

## 8. D-8：开关策略

建议不要复用 `ENABLE_LANGGRAPH_RUNTIME_EXECUTION` 作为唯一控制开关，而是新增一个更明确的 pilot 开关：

- `ENABLE_LANGGRAPH_EXTERNAL_PILOT`

原因：

- `runtime execution enabled`
  不等于
- `允许真实外部 pilot`

前者是 readiness 条件的一部分，后者是治理策略。

推荐语义：

- `ENABLE_LANGGRAPH_DRAFT_ADAPTER`
  - 允许注册占位 adapter
- `ENABLE_LANGGRAPH_RUNTIME_EXECUTION`
  - readiness 认为“执行条件满足”
- `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
  - 真正允许发出外部请求

这样不会把“配置看起来 ready”误等价成“允许实际调用外部框架”。

## 9. D-9：受控真实 Pilot

### 目标

在 D-8 的执行骨架存在后，D-9 再把它接到现有 pilot 治理链路，但仍限定在：

- 单 adapter
- 单请求
- 单次受控 pilot

不做：

- chat 主路径接管
- planner 子执行 fan-out
- 持续多轮外部会话

### 推荐入口

不建议复用当前 `POST /api/runtime-framework-adapters/pilot-run` 原语义直接强塞真实外部 adapter。

更稳的做法是二选一：

1. 保持现有接口，但加入：
   - adapter 级 allowlist
   - pilot mode 标记
2. 或新增：
   - `POST /api/runtime-framework-adapters/external-pilot`

从企业治理角度，我更倾向第 2 种，因为：

- 本地 fake pilot
  和
- 真实外部 pilot

本质上不是同一种风险等级。

## 10. D-9：最小验收标准

只有满足以下条件，才算 D-9 完成：

1. `langgraph_draft` 可以在受控开关下发起一次真实外部 pilot
2. 平台能拿到最小 status / output 事件
3. 失败时能明确区分连接失败、配置失败、协议失败、上游失败
   - probe 缺少 assistant identity evidence -> `protocol_error`
   - upstream 明确不识别 assistant identity -> `configuration_error`
4. 结果继续进入：
   - trace
   - audit
   - snapshot
   - Runtime Surface
   - Governance Timeline
5. 不改动 chat 主执行路径
6. 关闭 pilot 开关后，接口必须确定性拒绝执行

## 11. 推荐测试切分

### 后端单测

建议新增：

- `test_langgraph_request_translator.py`
- `test_langgraph_event_translator.py`
- `test_langgraph_runtime_client.py`

覆盖点：

- request shape 稳定
- 外部返回块映射稳定
- 错误分类稳定

### service 级测试

建议新增：

- `test_framework_adapter_runtime_service_external_pilot.py`

覆盖点：

- pilot 开关开启时可执行
- pilot 开关关闭时被拒绝
- trace / audit / snapshot 正常写入

### 前端回归

建议仅补最小回归：

- `RuntimeSurfacePanel`
  - 显示真实外部 pilot 可执行或被阻断状态
- `GovernanceTimelinePanel`
  - 能识别 `framework_adapter_external_error` 或真实外部 pilot 结果

## 12. 明确不做

D-8 / D-9 当前明确不做：

- 不接入 chat 正式主链路
- 不接入 planner fan-out 子执行
- 不做 LangGraph workflow 可视化编辑
- 不做 checkpoint 存储设计
- 不做多租户外部 runtime 凭证治理
- 不做外部 runtime 长连接池或 session 复用

这些事情都重要，但不该混进“第一次真实执行骨架落地”。

## 13. 推荐实施顺序

1. 新增 `LangGraphRequestTranslator`
2. 新增 `LangGraphRuntimeClient`
3. 新增 `LangGraphEventTranslator / OutputTranslator`
4. 新增 `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
5. 新增受控 external pilot service / route
6. 补齐 trace / audit / snapshot 映射
7. 补最小前后端回归

这个顺序的好处是，每一步都能单独验证，不会把问题全混在一起。

## 14. 可执行任务切片

为了避免 D-8 / D-9 落地时再次变成“大改一坨”，建议按下面 6 个 tracer bullet 小步推进。

### Slice 1：Translator 骨架

目标：

- 固定平台到外部 runtime 的最小 request 形状
- 不发真实请求
- Slice 1 是 D-8 的推荐第一落点，落成后不应修改任何 route、health 或前端行为。

建议改动文件：

- `backend/agent_framework/external/langgraph_translators.py`
- `tests/agent_framework/test_langgraph_request_translator.py`

最小交付：

- `LangGraphRequestTranslator.translate(...)`
- request shape 单测

完成定义：

- 输入 `run_id / messages / execution_context`
- 输出稳定 request dict
- 不读取 DB
- 不依赖网络

当前兼容性说明：

- 为了先锁定最小请求 contract，Slice 1 允许对消息 `role/content` 做兼容性归一化。
- 到 D-9 真实 external pilot 前，应重新评估是否需要把“缺失 role 默认 user”和“content trim”收紧为更显式的输入校验策略。

### Slice 2：Runtime Client 骨架

目标：

- 提供最小 client 接口
- 定义超时与错误包装
- 先用 stub transport 验证，不依赖真实 endpoint
- Slice 2 的 runtime client 只负责 transport 调用和错误包装，不负责 request shape、event mapping 或 trace 写入。

建议改动文件：

- `backend/agent_framework/external/langgraph_client.py`
- `tests/agent_framework/test_langgraph_runtime_client.py`

最小交付：

- `LangGraphRuntimeClient.invoke(...)`
- `LangGraphRuntimeClient.stream(...)`
- 最小错误分类：
  - `connectivity_error`
  - `authentication_error`
  - `protocol_error`
  - `upstream_runtime_error`

完成定义：

- transport 可注入 mock
- timeout 可配置
- 原始异常会被包装成平台可治理错误

### Slice 3：Event / Output Translator

目标：

- 固定外部 runtime -> 平台事件映射
- 让 trace / audit 继续只看到平台事件
- Slice 3 只生成平台 `AgentEvent` 字典并保留逻辑事件标记，不直接承担 trace/event_type 落库映射。

建议改动文件：

- `backend/agent_framework/external/langgraph_translators.py`
- `tests/agent_framework/test_langgraph_event_translator.py`

最小交付：

- `LangGraphEventTranslator.translate_chunk(...)`
- `LangGraphOutputTranslator.translate_final(...)`

完成定义：

- 至少能映射：
  - `framework_adapter_status`
  - `framework_adapter_output`
  - `framework_adapter_external_error`
- 保留 `adapter_id / framework_name / run_id`

### Slice 4：Pilot 开关与 Adapter 升级

目标：

- 把 draft adapter 从“只能 precheck”升级到“可在严格开关下允许 external pilot”
- 但默认仍关闭
- Slice 4 只在 SPI 层增加 external pilot gate，不直接开放任何真实执行入口。

建议改动文件：

- `backend/config.py`
- `backend/agent_framework/framework_adapters.py`
- `tests/agent_framework/test_framework_adapter_spi.py`

最小交付：

- `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
- `LangGraphDraftAdapter.can_execute()` 引入 pilot 策略判断

完成定义：

- `ready` 不自动等于“允许真实执行”
- 未开 pilot 开关时，接口必须明确拒绝

### Slice 5：受控 External Pilot Service / Route

目标：

- 给真实外部 adapter 提供单独 pilot 入口
- 不复用本地 fake pilot 的风险语义
- Slice 5 只新增独立 external-pilot route，不改 `pilot-run` 语义，也不接 chat 主路径。

建议改动文件：

- `backend/services/framework_adapter_runtime_service.py`
- `backend/routers/health.py`
- `backend/schemas_runtime_surface.py`
- `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`
- `tests/agent_framework/test_health_router.py`

最小交付：

- 推荐新增：
  - `POST /api/runtime-framework-adapters/external-pilot`
- service 层执行：
  - request translate
  - client invoke / stream
  - event translate
  - output translate
  - trace / audit / snapshot

完成定义：

- 开关开启时可执行
- 开关关闭时确定性拒绝
- 失败分类可进入返回与 timeline

### Slice 6：前端最小治理接入

目标：

- 前端只增加最小 external pilot 能力
- 不重做整个面板结构

建议改动文件：

- `frontend-vue/src/api/index.js`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`

最小交付：

- `RuntimeSurfacePanel` 在 `langgraph_draft` ready 且允许 pilot 时展示 `运行 External Pilot`
- 时间线能展示真实外部 pilot 成功或失败结果

完成定义：

- 不影响现有 `LocalFakeFramework Pilot`
- 不影响现有 `LangGraph Precheck`
- 出错时能看到治理语义，不只是一句通用报错

实施状态（2026-05-13）：

- 已完成
- `RuntimeSurfacePanel` 已新增：
  - `运行 External Pilot`
  - `最近 LangGraph External Pilot`
  - `查看时间线`
  - `复制快照命令`
- `GovernanceTimelinePanel` 已新增：
  - `framework_adapter_external_pilot_completed`
  - `framework_adapter_external_error`
  - `最近一次 LangGraph External Pilot`

## 15. 文件落点建议

为避免下一轮实现时文件扩散失控，建议先锁定落点：

后端：

- `backend/agent_framework/external/langgraph_client.py`
- `backend/agent_framework/external/langgraph_translators.py`
- `backend/agent_framework/framework_adapters.py`
- `backend/services/framework_adapter_runtime_service.py`
- `backend/routers/health.py`
- `backend/config.py`

前端：

- `frontend-vue/src/api/index.js`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`

测试：

- `tests/agent_framework/test_langgraph_request_translator.py`
- `tests/agent_framework/test_langgraph_runtime_client.py`
- `tests/agent_framework/test_langgraph_event_translator.py`
- `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`

## 16. 每个切片的回滚点

为了符合企业级渐进落地要求，D-8 / D-9 每一步都应有明确回滚点：

- Slice 1 回滚点：
  - translator 文件可单独删除，不影响现有 readiness / precheck
- Slice 2 回滚点：
  - client 骨架可删除，不影响 registry / doctor / timeline
- Slice 3 回滚点：
  - event translator 可删除，不影响 fake pilot
- Slice 4 回滚点：
  - 关闭 `ENABLE_LANGGRAPH_EXTERNAL_PILOT`
- Slice 5 回滚点：
  - 移除 `external-pilot` route，不影响 `precheck`
- Slice 6 回滚点：
  - 前端隐藏 external pilot 按钮，不影响现有治理卡

这很重要，因为真实外部 runtime 接入最容易出现“半接入半可用”的灰色状态。

## 17. 建议验收命令

下一轮开始实现后，建议每个切片都保持轻量验证，不要等最后一起验证。

后端建议分步执行：

```powershell
python -m unittest tests.agent_framework.test_langgraph_request_translator -v
python -m unittest tests.agent_framework.test_langgraph_runtime_client -v
python -m unittest tests.agent_framework.test_langgraph_event_translator -v
python -m unittest tests.agent_framework.test_framework_adapter_runtime_service_external_pilot tests.agent_framework.test_health_router -v
```

前端建议分步执行：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

如果进入集成收口，再补一组：

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_startup_diagnostics_service tests.agent_framework.test_doctor_script -v
```

## 18. 当前实现状态（2026-05-13）

当前 D-8 / D-9 骨架已经完成到 Slice 6，具体包括：

1. Slice 1
   - `LangGraphRequestTranslator` 已落地
2. Slice 2
   - `LangGraphRuntimeClient` 已落地
3. Slice 3
   - `LangGraphEventTranslator / LangGraphOutputTranslator` 已落地
4. Slice 4
   - `ENABLE_LANGGRAPH_EXTERNAL_PILOT` 已落地
5. Slice 5
   - `POST /api/runtime-framework-adapters/external-pilot` 已落地
6. Slice 6
   - `RuntimeSurfacePanel / GovernanceTimelinePanel` 已完成最小治理接入

当前 external pilot 已具备：

- 按钮触发
- 结果卡展示
- 失败治理语义展示
- snapshot 引用
- 复制快照命令
- 查看时间线
- `assistant_id / endpoint / probe` preflight
- `assistant identity evidence` preflight
  - `assistant_exists = true`
  - `assistant_id` 精确匹配
  - `assistants[]` 包含当前 id
- `configuration_error / connectivity_error / protocol_error` 的最小前置失败分类
  - 无 assistant evidence 或 evidence 形状非法 -> `protocol_error`
  - upstream 不识别当前 assistant identity -> `configuration_error`

当前仍保留的工程边界：

- 不接入 chat 主执行路径
- 不做多会话池与 checkpoint 管理
- 不做复杂 workflow authoring

## 19. 当前结论

当前最合理的下一步不再是“证明 external pilot 骨架存在”，因为这一步已经完成。更合理的是继续收紧 D-9 的工程化边界：

- 深化 transport / endpoint / assistant identity 校验
- 强化 external pilot 的失败分类与手工验收
- 保持不接入 chat 主路径的前提下，决定是否进入更深一层的受控 pilot

只要后续继续保持这个收敛策略，平台就能在不破坏既有治理边界的前提下，逐步把外部 framework 从 readiness 占位推进到真实可治理执行。
