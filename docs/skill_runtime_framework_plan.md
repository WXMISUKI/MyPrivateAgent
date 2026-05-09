# Skill Runtime 框架建设计划

## 目标

将 Skills 从 CRUD 管理资产提升为一次 Agent Run 中可被确定性选择、注入并审计的一等运行时参与者。

## 当前阶段

### Phase D1：运行时选择与注入

已实现：

- `backend/services/skill_runtime_service.py`
  - 从数据库存储中加载已启用 Skills
  - 解析 `SKILL.md` 的 frontmatter 和正文
  - 根据以下因素对运行时匹配结果打分：
    - 用户消息重叠度
    - `agent_role`
    - `required_capabilities`
    - 直接的 skill-name / trigger 命中
- `backend/orchestrator.py`
  - 将已选 Skills 作为运行时 system prompt context 注入
  - 发出 `status_kind=runtime_skills`
  - 持久化 `runtime_skill` 与 `runtime_skill_effect` artifacts
- `backend/services/chat_service.py`
  - 将 `runtime_skills` 状态归一化写入 planner `run_trace`

### Phase D2：优先级 / 激活 / 冲突策略

已实现：

- skill frontmatter 现已支持轻量级运行时治理字段：
  - `priority`
  - `activation` / `activation_mode`
  - `domain`
- 运行时现已支持：
  - `manual`：不自动选择
  - `role_only`：仅当 `agent_role` 匹配时才自动选择
- 运行时冲突解决会按确定性策略抑制重叠候选项：
  - 先比较更高的 runtime score
  - 再比较更高的 `priority`
  - 最后按稳定的 id / name 顺序决胜

## 为什么这一阶段重要

项目已经具备 planner、scheduler、MCP 和 runtime trace 的基础。如果没有运行时 Skill 选择能力，整个框架仍然更像是在使用静态 Skill 资产，而不是可主动参与执行的运行时构件。

这一阶段建立了最小成熟边界：

- 运行时可以解释为什么选择某个 Skill
- 被禁用或未命中的 Skills 不会污染执行过程
- 被选中的 Skills 会留下便于运营侧理解的 artifacts 和 trace records

## 当前边界

当前已经实现：

- 确定性的运行时 Skill 打分
- 确定性的优先级 / 激活 / 冲突策略
- Skill 感知的 system prompt 注入
- 运行时 Skill 选择结果在 planner trace 中可见
- 针对匹配与 artifact 持久化的回归测试

尚未实现：

- Skill 作为一等可调用运行时工具
- 前端运营控制台中的 Skill 命中归因
- Skill 优先级覆盖 / tenant / domain 隔离
- Skill 审批、回滚与治理工作流

## 推荐下一步

1. 将已选 Skills 绑定到 planner item / run records，而不是仅做 prompt 注入。
2. 将部分 Skills 提升为结构化的 tool / context adapter，而不是只注入纯文本片段。
3. 增加运营侧的 Skill 命中历史和 run 级 trace 查询视图。
4. 扩展治理能力，支持 tenant / domain 隔离和回滚工作流。
