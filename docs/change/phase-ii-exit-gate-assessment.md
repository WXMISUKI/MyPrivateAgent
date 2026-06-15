# Phase II Exit Gate Assessment

> 日期：2026-06-14
> 状态：初版评估
> 来源：`openspec/changes/add-phase-ii-exit-gate-assessment`

## 1. 评估背景

Phase II 自启动以来，围绕四个子任务推进：

| 子任务 | 状态 | 说明 |
|--------|------|------|
| II-1: Embedded SDK persistence/recovery | 进行中 | 边界定义完成，实现扩展待定 |
| II-2: Governance Timeline 前端拆分 | 进行中 | 首轮拆分完成，继续提取中 |
| II-3: Runtime Surface assembler | 进行中 | 部分 builder 已提取 |
| II-4: Phase II Exit Gate | 未开始 | 本文档即为该任务的产出 |

## 2. 收束标准逐项评估

### 标准 1：SDK persistence/recovery 达到下一成熟度

**当前状态：边界定义完成，实现扩展待定**

已完成：
- `persistence_interface` 姿态定义（`memory_preview` / `durable_ready` / `durable_degraded`）
- `EmbeddedRunWorkspaceStore` 协议 + `InMemoryEmbeddedRunWorkspaceStore` 实现
- continuation descriptor 持久化边界
- recovery probe（`probe_run_recovery()`）
- checkpoint/cursor probe
- recovery operation evidence contract
- worker ownership store（in-memory + SQLAlchemy durable adapter）
- production recovery gate contract
- child executor promotion gate、dispatch contract、sandbox backend
- 大量 smoke/gate/snapshot 覆盖

未完成：
- 实际 durable backend 接入（当前仍是 memory_preview）
- 跨进程 recovery（当前仅 in-process reattach）
- worker lease production gate（当前 blocked）
- failure retry scheduler（当前 opt-in seam only）
- real child executor dispatch（当前 `will_dispatch=false`）

**评估：边界成熟度已达"可扩展"水平，但未达"可生产"水平。**

### 标准 2：Governance 前端拆分为更稳定边界

**当前状态：首轮拆分完成**

已完成（10 个子组件已提取）：
- `GovernanceTimelineFilters.vue`（1,648 bytes）
- `GovernanceTimelineEventCard.vue`（7,978 bytes）
- `GovernanceTimelineMainChatWorkspace.vue`（3,077 bytes）
- `GovernanceTimelineFocusSummaryGrid.vue`（9,913 bytes）
- `GovernanceTimelineEventStream.vue`（4,404 bytes）
- `GovernanceTimelineFrameworkAdapterCards.vue`（8,051 bytes）
- `GovernanceTimelineSummaryActionCards.vue`（6,311 bytes）
- `GovernanceTimelineOverviewCards.vue`（1,974 bytes）
- `GovernanceTimelineFrameworkAdapterRemediationCard.vue`（2,714 bytes）
- `GovernanceRecentSnapshotCommandsCard.vue`（3,563 bytes）

未完成：
- `GovernanceTimelinePanel.vue` 仍有 1,208 行（39,626 bytes）
- remediation card 和 snapshot command card 可进一步提取
- 边界稳定化（组件间接口尚未形式化）

**评估：首轮拆分有意义，但主面板仍大于 1,000 行，需继续拆分。**

### 标准 3：Runtime Surface assembler 方法明确并开始落地

**当前状态：部分提取完成**

已完成：
- `RuntimeSurfaceProfileAssembler` 已提取到独立文件
- `RuntimeSurfaceProfileContextAssembler` 处理 profile request context
- `RuntimeCoreContractBuilder` 处理 runtime_core shell/scope/child merge

未完成：
- `RuntimeSurfaceService.py` 仍有 1,243 行
- governance overview builder 未提取
- deeper concern-specific builders 未提取
- 测试覆盖未闭合

**评估：方向明确，但提取进度约 40%。**

### 标准 4：团队能判断何时回到 channel 实现 vs 留在基础设施主线

**当前状态：SDK 路径已证明可用，但缺乏明确的切换标准**

已完成：
- SDK 路径端到端验证（model_step → tool_executor → reviewer → governance trace）
- 域 agent SDK 执行集成（`POST /api/agents/{agent_id}/execute`）
- 参考域 agent（天气助手）
- 端到端烟雾测试

未完成：
- 缺乏明确的"何时回到 channel 实现"标准
- 缺乏 Phase III 方向共识
- SDK persistence/recovery 未达生产水平

**评估：SDK 路径已证明可用，但切换标准未定义。**

## 3. 总体评估

| 标准 | 完成度 | 评级 |
|------|--------|------|
| SDK persistence/recovery | 边界定义完成，实现扩展待定 | ⚠️ 60% |
| Governance 前端拆分 | 首轮拆分完成，继续提取中 | ⚠️ 50% |
| Runtime Surface assembler | 部分提取完成 | ⚠️ 40% |
| 团队判断标准 | SDK 已证明可用，标准未定义 | ⚠️ 50% |

**总体评级：Phase II 尚未达到收束标准，但已有实质性进展。**

## 4. 建议

### 选项 A：继续 Phase II，聚焦剩余工作

**聚焦 II-2（Governance 前端拆分）**：
- 继续提取 remediation card 和 snapshot command card
- 把 `GovernanceTimelinePanel.vue` 降到 800 行以下
- 形式化组件间接口

**聚焦 II-3（Runtime Surface assembler）**：
- 继续提取 governance overview builder
- 把 `RuntimeSurfaceService.py` 降到 800 行以下
- 闭合测试覆盖

**预计工作量：2-3 个 OpenSpec change**

### 选项 B：关闭 Phase II，进入 Phase III

**理由：**
- SDK 路径已证明可用（最重要的基础设施已就绪）
- 继续 Phase II 的收益递减（前端拆分是改善，不是突破）
- Phase III 的方向更清晰（persistence/recovery、domain agent marketplace）

**风险：**
- Governance 前端仍大于 1,000 行
- Runtime Surface assembler 未完成
- 切换标准未定义

### 选项 C：混合方案

**定义 Phase II 最低收束标准，满足后进入 Phase III：**
1. SDK 路径端到端验证 ✅（已完成）
2. 域 agent SDK 执行集成 ✅（已完成）
3. Governance 前端拆分到 1,000 行以下（需继续）
4. Runtime Surface assembler 提取到 1,000 行以下（需继续）
5. 定义"何时回到 channel 实现"标准（需定义）

**预计工作量：3-4 个 OpenSpec change**

## 5. 推荐

**推荐选项 C（混合方案）。**

理由：
1. SDK 路径已证明可用——这是 Phase II 最重要的产出
2. 继续 Phase II 的收益递减——前端拆分是改善，不是突破
3. Phase III 的方向更清晰——persistence/recovery、domain agent marketplace
4. 但需要设定最低收束标准——避免带着未完成的工作进入 Phase III

**具体建议：**
1. 完成 Governance 前端拆分（2 个 change）
2. 完成 Runtime Surface assembler 提取（1 个 change）
3. 定义"何时回到 channel 实现"标准（1 个 change）
4. 关闭 Phase II，进入 Phase III

## 6. Phase III 方向建议

基于 Phase II 的产出，Phase III 的自然方向是：

1. **SDK persistence/recovery 实现**——从边界定义到实际 durable backend
2. **域 agent marketplace**——从单个参考 agent 到多 agent 注册和发现
3. **Streaming adapter**——从同步执行到 SSE 事件流
4. **child executor 实现**——从 `relationship_only` 到真实委托

**优先级建议：persistence/recovery > streaming > child executor > marketplace**

---

*本文档为初版评估，需团队讨论后确认最终方向。*
