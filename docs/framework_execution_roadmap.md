# 通用智能体框架实施清单

本文档用于收口 `MyPrivateAgent` 作为通用智能体框架 demo 的后续完善方向。目标不是继续堆单点工具，而是让当前项目更接近 Claude Code 一类成熟智能体的执行链、治理层与运行时配置面。

## 总目标

- 建立稳定的主智能体身份与能力边界
- 形成完整的执行闭环：意图识别、计划、工具调用、结果消费、完成度评估、最终答复
- 建立可配置的 Provider / Model Runtime Surface
- 建立能力缺口统计闭环，为后续垂域智能体建设提供依据

## 阶段一：主智能体治理层

### 目标

- 让主智能体显式知道“我是谁、我会什么、我不会什么”
- 让运行时界面可直接看到当前能力合同

### 工作项

1. 统一 `Agent Identity Prompt`
2. 统一 `Capability Profile`
3. 统一能力边界输出结构：
   - 已完成
   - 当前缺口
   - 建议补强能力
4. 将能力合同接入 `/api/runtime-profile`
5. 在设置页展示主智能体身份、执行原则、可用能力、受限能力

### 验收标准

- 复杂请求下，模型能更稳定输出能力边界说明
- 设置页可以直接看到当前主智能体身份与能力合同
- 运行时信息不再只是 provider/model 列表

## 阶段二：执行闭环增强

### 目标

- 让工具调用成为中间观察，而不是草率终止
- 建立轻量完成度评估

### 工作项

1. 复合任务的 `final synthesis` 规则继续收口
2. 建立 `completion evaluator`
3. 对常见复合请求定义最小完成标准
4. 增加一次补查策略
5. provider / tool 重试与降级策略标准化
6. 将 `completion_retry / completion_finalized / capability_gap_fallback` 写入 run trace，形成可观测执行链
7. 从单一旅行类闭环推广到通用复合任务模板，例如 `travel / research-compare / planning`
8. 统一 provider / tool 错误分类，为后续重试、降级、治理台统计提供结构化基础
9. 将 `completion profile / completion stage / error category` 接入 run trace 与治理统计，支撑成熟执行治理分析

### 验收标准

- 复合任务不再只停留在工具结果卡片
- 返回内容能区分“完成”和“部分完成”
- 超时、无结果、能力不足三类场景有明确降级路径
- 治理台可以区分不同复合任务模板、收尾阶段与错误类型

## 阶段三：运行时配置面

### 目标

- 让 provider / model 切换成为配置问题，而不是代码问题

### 工作项

1. 完善 Provider Registry
2. 完善 Model Catalog
3. Ollama 本地模型探测继续稳定化
4. 运行时配置分层：
   - `.env`
   - `.myagent/runtime_surface.json`
   - 前端设置页
5. 后续支持 provider 启停、模型别名与默认模型治理
6. 在设置页清晰展示配置来源、可编辑范围和当前生效值
7. 将 provider 启停纳入本地运行时覆写，避免模型切换仍依赖前端硬编码或后端固定常量

### 验收标准

- 前端模型列表完全来自后端目录
- 默认模型与鉴权模式可安全持久化
- 后续新增 provider 不需要改前端常量
- 设置页可以看出配置是来自默认值还是本地覆写

## 阶段四：Demo / Business 模式分层

### 目标

- demo 开箱即用
- business 模式后续可无缝接入真实认证

### 工作项

1. 默认 `demo_guest`
2. 设置页明确展示当前鉴权模式
3. 预留 `business_auth` 扩展位
4. 登录页改为业务模式入口，而不是 demo 主入口
5. 在设置页和运行时能力面明确区分 demo 演示假设与 business 接入假设

### 验收标准

- demo 一启动即可进入 chat
- business 模式切换后不会破坏现有框架结构

## 阶段五：能力缺口治理闭环

### 目标

- 让框架能帮助开发者识别“该补哪类能力”

### 工作项

1. 继续汇总 `capability_gap_fallback`
2. 增加按类型、时间、计划项的统计视图
3. 建议补强方向归类：
   - 工具
   - Skill
   - MCP
4. 后续支持 provider / model 维度的能力缺口对比
5. 支持按缺口类型、关键词做筛选，便于从汇总盘点进入定向治理
6. 支持按复合任务模板、收尾阶段、错误类型做筛选与聚合

### 验收标准

- 能从真实请求中看出高频缺口
- 可以指导后续垂域智能体补强顺序

### 阶段五状态定义

- `V1（当前目标）`：
  - 打通能力缺口事件采集、聚合、筛选、前端展示
  - 维度至少覆盖 `profile / completion_stage / error_category / hook_event_type / subagent_role`
  - 可形成“已完成、缺口、补强建议”的治理闭环
- `V2（后续增强）`：
  - 增加跨 provider/model 的时序与对比分析
  - 增加更细粒度的趋势与回归看板
  - 增加更系统的治理报表导出能力

## 当前建议优先顺序

1. 阶段一：主智能体治理层
2. 阶段三：运行时配置面
3. 阶段二：执行闭环增强
4. 阶段五：能力缺口治理闭环增强
5. 阶段四：Demo / Business 模式持续收口

## 最新进展（2026-04-28）

- 已落地分层记忆 / 指令系统最小闭环：
  - `GLOBAL_AGENT.md`
  - `PROJECT_AGENT.md`
  - `agent_memory_service`
  - runtime profile 中的 `memory_contract`
- 已落地 Subagent 正式注册能力面最小版本：
  - `researcher / planner / executor` 注册信息
  - 角色描述、工具范围、模型偏好、触发条件
  - runtime profile 中的 `subagent_contract`
- 已落地 Hooks / Permission 治理层最小版本：
  - `pre_tool_use / post_tool_use / on_fallback`
  - 高风险工具关键字阻断策略（默认最小策略）
  - runtime profile 中的 `hook_contract`
  - AgentHarness 主链路已接入 pre/post/fallback hook
  - hook 事件已接入 run trace（可区分治理阻断与普通权限拒绝）
- 已推进 Subagent 调度对齐：
  - 调度器角色推断已优先使用 Subagent 注册触发条件，再回退 legacy 关键字规则
- 已推进阶段五治理台联动：
  - 能力缺口统计已支持 `hook_event_type` 与 `subagent_role` 维度
  - 可在同一视图联动筛选 `profile / completion_stage / error_category / hook / subagent`
- 已推进阶段五 V2 第一批：
  - 能力缺口统计新增 `provider / model` 维度聚合与筛选
  - 治理面板可联动筛选 `provider` 与 `model_name`
  - run trace 映射已为关键事件补充 `model_name / provider` 字段透传
  - 能力缺口统计新增 `window_days(7/14/30)` 时间窗口过滤
  - 新增 `profile-provider-model` 三维组合对比，支持按模板与模型联动分析
  - 新增时间窗口环比：本窗口 vs 上窗口 缺口事件变化
  - 新增 Top 回归风险模型：按窗口增量识别高风险 provider/model 组合
  - 新增阶段六最小评测包：回归健康度（4个关键断言）并接入能力缺口看板
  - 新增阶段六门禁阈值：回归健康度默认阈值 80 分，并输出 gate 状态
  - CI 已纳入能力缺口治理相关测试，防止执行链回归无感进入主分支
  - 新增固定 benchmark 用例集（`backend/config/benchmark_cases.json`）并纳入覆盖率门禁
  - 新增固定用例场景分组与失败原因输出（缺事件/缺字段/超预算），用于快速定位回归根因
  - 新增失败原因到修复建议映射，治理看板可直接给出整改方向
  - 新增整改动作 ID 与动作手册（action playbook），为后续 /doctor 自动化整改预留标准动作层
- 阶段五 `V1` 验收已通过（代码、测试、界面联动）：
  - 后端单测通过（41 项）：`python -m unittest tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_subagent_service tests.agent_framework.test_capability_gap_service tests.agent_framework.test_health_router`
  - 前端单测通过（33 项）：`npm test`
  - 前端构建通过：`npm run build`

## 阶段五验收结论（2026-04-28）

- 结论：`阶段五 V1 已完成`，`阶段五 V2 未完成（按规划后续推进）`
- 已完成能力：
  - 缺口事件与执行阶段链路已稳定采集
  - hook/subagent 治理维度已进入 run trace 与缺口聚合
  - 治理面板已支持多维筛选与聚合展示
  - 能输出可行动的补强方向（工具 / Skill / MCP）
- 后续建议（进入下一阶段）：
  - 补齐 provider/model 跨模型质量看板
  - 补齐时序趋势、回归对比、导出能力
