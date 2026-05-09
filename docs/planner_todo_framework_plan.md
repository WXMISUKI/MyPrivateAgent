# Planner Todo 框架建设计划

## 目标

在当前可复用的 Agent Demo 之上，构建一层 Claude Code 风格的最小 Planner / Todo 能力，让项目不再只是“chat + tools”，而是具备“goal -> plan -> execution state”的执行链路。

## 本阶段范围

1. 增加后端 planner 领域模型。
2. 增加 planner service 与 REST API。
3. 增加前端 planner store 与可复用面板组件。
4. 将 planner panel 集成到 chat view。
5. 补充实现日志，并保持 docs 索引同步更新。

## 本阶段已交付

- `backend/models.py`
  - 新增 `PlanStatus`
  - 新增 `PlanRunRecord`
  - 新增 `PlanItemRecord`
- `backend/services/planner_service.py`
  - Plan CRUD
  - Item CRUD
  - 单一激活中的 `in_progress` item 约束
  - 进度汇总刷新
  - 基于目标文本的最小自动生成计划能力
- `backend/routers/plans.py`
  - `GET /api/plans`
  - `POST /api/plans`
  - `POST /api/plans/generate`
  - `GET /api/plans/{plan_id}`
  - `PATCH /api/plans/{plan_id}`
  - item 的新增 / 更新 / 删除接口
- `frontend-vue/src/stores/planner.js`
  - 加载 / 创建 / 生成 / 更新 / 新增 / 删除 plan 的 actions
- `frontend-vue/src/components/PlannerPanel.vue`
  - planner / todo 面板 UI
- `frontend-vue/src/views/ChatView.vue`
  - planner panel 集成
  - 基于聊天输入的 objective draft
  - 内联 “generate plan” 入口
- 聊天执行集成
  - 请求开始时将当前 plan item 标记为 `in_progress`
  - assistant 成功完成时将当前 item 标记为 `completed`
  - 后端发出 `plan_updated` SSE 事件
  - 前端会话流根据运行时事件刷新 planner store
- planner 分配语义
  - plan item 现已支持 `agent_role`
  - plan item 现已支持 `agent_id`
  - plan item 现已支持 `handoff_status`
  - 自动生成的 plan item 会带启发式初始角色建议
- 最小运行时 handoff loop
  - chat 启动时会发出针对 `in_progress` 的 `plan_updated`
  - 专业化 plan item 会经历 `ready -> handed_off -> executing -> merged`
  - orchestrator 现在会接收 `execution_context`
  - orchestrator 会在伪 subagent 模式下发出运行时 `status`
  - stream / non-stream 两条 chat 路径都会保持 planner 状态流转一致
- 最小 spawned subagent runtime
  - 新增 `SubagentRuntimeService`
  - 专业化 plan item 现在会创建隔离的 subagent execution context
  - orchestrator 会发出 `subagent_spawned -> subagent_collected -> subagent_merged`
  - 面向角色的 system prompt 已经由独立 subagent runtime layer 构建
- planner capability enforcement
  - active plan item 在执行开始前会校验 `required_capabilities`
  - 缺失 / 不可用能力会阻断 plan item，而不是静默继续
  - chat route 会返回确定性的 blocked response 和 planner 状态更新
- MCP execution bridge
  - MCP capability tools 不再停留在 placeholder text
  - stdio provider 现在通过子进程 stdin/stdout 接收 JSON payload
  - http provider 现在通过 runtime adapter 接收 JSON POST 请求

## 为什么这很重要

- 它为后续多智能体编排建立了一层一等执行状态。
- 它让 Demo 不再只有会话式 UX，而是具备可见、可复用的计划能力。
- 它为后续工作建立了稳定的 API 和 UI 边界：
  - planner events
  - subagent assignment
  - approval checkpoints
  - 基于 MCP 的任务执行

## 已知缺口

- 当前 handoff 仍然是伪 subagent 协议，不是真正的 spawned worker runtime。
- `agent_id` 现在已经是稳定的运行时元数据，但还没有独立的执行容器 / 线程作为承载。
- Planner 事件目前仍由 chat 集成层发出，而不是来自通用 orchestrator / harness event bus。
- 还没有 planner 专属前端测试。
- 还没有独立的 planner 页面或 timeline；当前入口仍嵌在 chat view 中。
- 还没有并行 child scheduler；当前 subagent runtime 仍是隔离但单进程、单 child。
- MCP registry 和最小运行时分发已经存在，但仍缺少完整的 MCP session / connector 层。

## 推荐下一步

1. 增加并行 child scheduler，实现真正的多 subagent fan-out / fan-in。
2. 从共享 orchestrator / harness event layer 发出 planner runtime events，而不是只走 chat route。
3. 增加 planner store / component 测试，以及一个端到端 planner smoke test。
4. 增加 `/plan`、`/todo`、`/focus` 等 planner commands。
5. 增加 planner timeline 或 audit log。
6. 增加 scheduler 级 capability policy、fallback strategy 和 MCP 执行审计链路。
