# Phase 44 实施记录：Skill Priority / Activation / Conflict Policy 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

在 Skill Runtime 第一版的基础上，补齐最小治理能力，让 Skill 选择不只是“能命中”，而是“可控、可解释、可稳定复现”。

## 本次实施范围

### 1. Skill Frontmatter 增加运行时治理字段

- 文件：`backend/services/skill_runtime_service.py`

当前支持从 `SKILL.md` frontmatter 读取：

- `priority`
- `activation` / `activation_mode`
- `domain`

其中：

- `priority`
  - 支持数值
  - 也支持 `critical / high / medium / low`
- `activation`
  - 当前支持：
    - `auto`
    - `manual`
    - `role_only`
    - `always`（当前等同 `auto`）

### 2. Activation Policy 第一版

当前运行时已支持：

- `manual`
  - 不参与自动匹配
  - 适合只想保留为人工指定的 Skill

- `role_only`
  - 只有当前 `execution_context.agent_role` 命中时才参与自动选择

这样一来，Skill 不再只是“只要文本沾边就可能被注入”，而是开始受显式策略控制。

### 3. Conflict Resolution 第一版

运行时现在会对候选 Skill 进行冲突压制：

- 优先按 runtime score 排序
- score 相同再比较 `priority`
- 再按稳定顺序打破平局

当前冲突键优先使用：

- `domain`
- 其次是 `agent_roles`
- 最后才退化到 `skill name`

被压制的 Skill 不会悄悄消失，而是会进入：

- `skipped_skills`
- `metadata.skipped_items`

原因标记为：

- `conflict_suppressed`

## 新增/更新测试

### 后端

- `tests/agent_framework/test_skill_runtime_service.py`
  - 验证 `manual` Skill 不会自动启用
  - 验证 `role_only` Skill 仅在匹配角色时启用
  - 验证同域 Skill 冲突时高优先级候选胜出

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_orchestrator_service tests.agent_framework.test_chat_service
```

- 27 条用例通过

## 当前阶段价值

这一步的意义在于，Skill Runtime 开始具备最小企业级治理能力：

- 可以控制哪些 Skill 允许自动进入运行时
- 可以限制某些 Skill 只在指定角色下生效
- 可以在候选重叠时稳定压制冲突

这使 Skill Runtime 更接近成熟智能体框架的“Instructions / Skills 选择层”，而不是简单文本堆叠。

## 当前仍然存在的缺口

- Skill 命中还没有绑定到 run/session 级视图
- Skill 仍主要以 prompt 注入参与执行，不是结构化工具或上下文适配器
- 还没有 tenant / project / domain 级隔离继承
- 还没有 rollback / approval / review workflow

## 下一步建议

1. 把 Skill 命中记录绑定到 run/session 级记录和查询接口
2. 逐步把部分 Skill 升级为结构化上下文或工具适配器
3. 再补 tenant / domain isolation 与 rollback 治理
