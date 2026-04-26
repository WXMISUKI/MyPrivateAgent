# Phase 43 实施记录：Skill Runtime Selection / Injection 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

把 Skill 从“后台可管理资产”推进到“运行时可选择、可注入、可留痕”的第一版能力，开始进入 agent 决策链，而不再只停留在 CRUD 和静态存储层。

## 本次实施范围

### 1. 新增 Runtime Skill Service

- 文件：`backend/services/skill_runtime_service.py`

新增 `SkillRuntimeService`，当前支持：

- 从数据库加载已启用 Skills
- 读取 Skill 存储目录下的 `SKILL.md`
- 解析 frontmatter 与正文
- 根据以下信号做确定性匹配：
  - 用户消息词项重叠
  - `execution_context.agent_role`
  - `required_capabilities`
  - skill 名称 / trigger 直接命中
- 生成 `RuntimeSkillContext`

当前 `RuntimeSkillContext` 会保留：

- `system_prompt`
- `selected_skills`
- `skipped_skills`
- `selected_items / selected_skill_ids / selected_skill_names`

### 2. Skill Runtime 接入 Orchestrator

- 文件：`backend/orchestrator.py`
- 文件：`backend/services/orchestrator_service.py`

当前 orchestrator 在每次执行时会：

- 调用 `SkillRuntimeService.get_runtime_context()`
- 在 Skill 命中时发出：
  - `type=status`
  - `status_kind=runtime_skills`
- 将 Skill 生成的 runtime prompt 作为 `SystemMessage` 注入执行链
- 持久化以下 artifact：
  - `runtime_skill`
  - `runtime_skill_effect`

这意味着 Skill 已经不是“只有管理页看得到”，而是开始真实参与单次执行。

### 3. Skill Runtime 进入统一 Run Trace

- 文件：`backend/services/chat_service.py`

新增运行时事件归一化：

- `status_kind=runtime_skills`
  - `source=skill`
  - `event_type=runtime_skills_selected`

当前 Planner 计划项的 `run_trace` 已经可以看到：

- 当前运行选择了几个 Skill
- 命中的 Skill 名称
- 关联的 `agent_role`

## 新增/更新测试

### 后端

- `tests/agent_framework/test_skill_runtime_service.py`
  - 验证按用户消息和 `agent_role` 选择匹配 Skill
  - 验证未命中 Skill 会被跳过

- `tests/agent_framework/test_orchestrator_service.py`
  - 验证 `runtime_skill` artifact 持久化
  - 验证 `runtime_skill_effect` artifact 持久化

- `tests/agent_framework/test_chat_service.py`
  - 验证 `runtime_skills` 状态事件会被映射到统一 `run_trace`

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_orchestrator_service tests.agent_framework.test_chat_service
```

- 24 条用例通过

## 当前阶段价值

这一步的价值不在于“Skill 功能多了一个页面”，而在于框架边界开始变对了：

- Skill 从静态资产变成运行时选择对象
- Agent 可以解释为什么命中某个 Skill
- Skill 选择结果可以进入 artifact 和 planner trace

这使项目更接近 Claude Code 式框架里“Instructions / Skills 进入 runtime 决策链”的成熟方向。

## 当前仍然存在的缺口

- Skill 仍然主要以 prompt 注入形式参与运行，还不是结构化 runtime tool
- 还没有显式 skill priority / conflict policy
- 还没有 run/session 级 skill hit 查询视图
- 还没有 skill 审批、回滚、域隔离和治理模型

## 下一步建议

1. 给 Skill 增加显式 priority / activation policy / conflict resolution
2. 把 Skill 命中记录绑定到 planner item / run 级数据，而不只是 prompt 和 trace
3. 逐步把部分 Skill 从“文本注入”升级成“结构化上下文或工具适配器”
