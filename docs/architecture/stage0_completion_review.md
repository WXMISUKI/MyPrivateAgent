# Stage 0 完成回顾：冻结与定位收口

> 日期：2026-07-05
> 阶段：Stage 0（运行层集成战略第一步）
> 状态：**已完成**

## 目标

明确方向，停止扩展，建立边界。为 Stage 1（运行层 MVP）打好文档和规范基础。

## 完成标准与产出

| # | 完成标准 | 产出 | 状态 |
|---|---|---|---|
| 1 | 项目定位文档更新 | `PROJECT_AGENT.md` 已从"通用智能体框架 demo"升级为 Control Plane 定位 | ✅ |
| 2 | 运行层集成战略文档 | `docs/architecture/runtime_plane_integration_strategy.md` 已创建，含目标架构、分层定义、ExecutionAdapter 合同、四阶段计划、10 条硬约束 | ✅ |
| 3 | OpenSpec spec 创建 | `openspec/specs/runtime-plane-integration-strategy/spec.md` 已创建，含 5 个 requirement + scenario 验收标准 | ✅ |
| 4 | 定位 spec 更新 | `openspec/specs/agent-runtime-control-plane-positioning/spec.md` 已增加"Control Plane Must Not Expand Into Execution Platform" requirement | ✅ |
| 5 | entrypoint 文档更新 | `docs/architecture/agent_runtime_control_plane_entrypoint.md` 已增加运行层引用、暂停线、阅读顺序 | ✅ |
| 6 | current_architecture 更新 | `docs/architecture/current_architecture.md` 已增加运行层战略说明和新约束 | ✅ |
| 7 | runtime_contracts 更新 | `docs/architecture/runtime_contracts.md` 已增加 ExecutionAdapter 合同概念 | ✅ |
| 8 | extension_points 更新 | `docs/architecture/extension_points.md` 已增加运行层 adapter 说明 | ✅ |
| 9 | 目录骨架创建 | `backend/control_plane/` 和 `backend/runtime_plane/` 含 `__init__.py` + `README.md` 骨架 | ✅ |
| 10 | AgentHarnessFacade 冻结 | 不再新增 preview 方法，保持现有能力用于本地 smoke 和 adapter demo | ✅ 立即生效 |

## 产出文件清单

### 新建文件（11 个）

| 文件 | 用途 |
|---|---|
| `docs/architecture/runtime_plane_integration_strategy.md` | 核心战略文档 |
| `openspec/specs/runtime-plane-integration-strategy/spec.md` | 正式 OpenSpec spec |
| `docs/architecture/stage0_completion_review.md` | 本回顾文档 |
| `backend/control_plane/__init__.py` | 控制面目录骨架 |
| `backend/control_plane/README.md` | 控制面目录说明 |
| `backend/runtime_plane/__init__.py` | 运行层面目录骨架 |
| `backend/runtime_plane/README.md` | 运行层面目录说明 |
| `backend/runtime_plane/contracts/__init__.py` | 合同模块骨架 |
| `backend/runtime_plane/contracts/README.md` | 合同模块说明 |
| `backend/runtime_plane/adapters/__init__.py` | 适配器模块骨架 |
| `backend/runtime_plane/adapters/README.md` | 适配器模块说明 |
| `backend/runtime_plane/gateway/__init__.py` | 网关模块骨架 |
| `backend/runtime_plane/gateway/README.md` | 网关模块说明 |

### 更新文件（7 个）

| 文件 | 变更 |
|---|---|
| `PROJECT_AGENT.md` | 从"demo"升级为 Control Plane 定位，加入 10 条硬约束 |
| `docs/architecture/agent_runtime_control_plane_entrypoint.md` | 增加运行层引用、新暂停线、阅读顺序更新 |
| `docs/architecture/current_architecture.md` | 增加运行层战略说明、新架构约束 |
| `docs/architecture/runtime_contracts.md` | 增加 ExecutionAdapter 合同概念 |
| `docs/architecture/extension_points.md` | 增加运行层 adapter 说明 |
| `openspec/specs/agent-runtime-control-plane-positioning/spec.md` | 增加"不膨胀为执行平台"requirement |

## 10 条硬约束确认

| # | 约束 | 文档位置 | 状态 |
|---|---|---|---|
| 1 | 新 agent 必须有 agent.yaml | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 2 | 运行框架只通过 adapter 接入 | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 3 | 不实现通用 checkpoint/scheduler/sandbox | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 4 | 高风险工具走 policy/approval | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 5 | runtime_plane 只产出标准事件 | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 6 | control_plane 只消费标准事件 | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 7 | 新能力先写 OpenSpec | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 8 | adapter 必须有 promotion gate | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 9 | agent 必须有最小 eval/smoke | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |
| 10 | 禁止顺手扩展平台能力 | PROJECT_AGENT.md + strategy.md | ✅ 已写入 |

## 下一步：Stage 1 准备

Stage 0 已完成文档和规范基础。进入 Stage 1 前需要：

1. **选择 PoC 框架**：LangGraph（复杂编排 PoC）和/或 AgentRun（托管运行 PoC）
2. **选择 2-3 个典型 Coze 工作流**：一个简单问答、一个工具调用、一个需要审批的流程
3. **定义 ExecutionAdapter v1 实现**：在 `backend/runtime_plane/contracts/` 中实现标准 envelope
4. **实现第一个 LangGraphAdapter**：基于现有 `LangGraphDraftAdapter` 骨架升级
5. **创建第一个 domain_agent PoC**：在 `backend/domain_agents/` 下新增，含完整 agent.yaml + prompts + tools + evals

**预计时间**：2-3 周
**产出**：三个 demo agent（simple/tool/approval）、统一 Execution envelope、LangGraphAdapter 最小实现、trace 回传到治理层
