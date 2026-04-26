# Framework Phase 28 实施记录

## 日期
2026-04-24

## 主题
Runtime Knowledge 治理增强：`scope / enabled / rollback / effect tracking`

## 背景
Phase 26 已经引入了 `enforced / advisory / diagnostic` 三层治理，但距离成熟 harness 风格的 runtime knowledge 仍然差一层：

- 缺少作用域控制（scope）
- 缺少显式启停（enabled）
- 缺少回滚（rollback）
- 缺少运行效果追踪

如果没有这层，所谓“自学习注入”仍然容易逐渐失控。

## 本次目标

在不改数据库结构的前提下，基于现有字段：
- `SystemPrompt.tags`
- `SystemPrompt.is_active`
- `BestPractice.tags`
- `BestPractice.trade_offs`

做出一层真正可运行的治理规则。

## 本次改动

### 1. Runtime Knowledge 支持 scope / enabled / rollback
- 文件：`backend/services/runtime_learning_service.py`

新增规则：

#### 通用规则
- `scope:<name>`：限定知识只在指定 scope 生效
- `disabled` / `inactive`：不注入
- `rollback` / `rollback:<id>`：不注入

#### SystemPrompt
- `is_active=False` => 不注入
- `tags` 支持：
  - `scope:chat`
  - `disabled`
  - `rollback`

#### BestPractice
- `trade_offs.runtime.enabled`
- `trade_offs.runtime.scope`
- `trade_offs.runtime.rollback`
- `trade_offs.runtime.rollback_reason`

当前 orchestrator 默认使用：
- `scope="chat"`

只有满足：
- enabled
- 非 rollback
- scope 匹配
- 非 diagnostic

的知识，才会进入 runtime system prompt。

### 2. Runtime metadata 增加 selected/skipped trace
`RuntimeKnowledgeContext.metadata` 新增：
- `scope`
- `selected_items`
- `skipped_items`

这样每次运行不仅知道“注入了什么”，还知道“哪些知识为什么没被注入”。

这对于成熟框架非常关键，因为它让知识治理从“隐式”变成了“可审计”。

### 3. Runtime Knowledge Effect Artifact
- 文件：`backend/services/orchestrator_service.py`
- 文件：`backend/orchestrator.py`

新增：
- `persist_runtime_knowledge_effect_artifact()`

每次运行完成后，如果本次有命中的 runtime knowledge，会生成一个：
- `kind="runtime_knowledge_effect"`

记录内容包括：
- `scope`
- `selected_items`
- `selected_count`
- `stop_reason`
- `output_length`
- `prompt_keys`
- `practice_ids`

这一步让“知识命中了，但是否实际产生效果”开始具备最小追踪能力。

## 测试

### 新增/更新
- `tests/agent_framework/test_runtime_learning_service.py`
- `tests/agent_framework/test_orchestrator_service.py`

覆盖内容：
- `scope` 过滤
- `disabled` 过滤
- `rollback` 过滤
- `runtime_knowledge_effect` artifact 持久化

## 验证结果
- 定向测试：10 项通过
- 完整后端测试：61 项通过

## 结果
这一步之后，runtime knowledge 已经不再只是“能注入”：

而是具备了成熟 harness 常见的最小治理能力：

- 能限定范围
- 能停用
- 能回滚
- 能追踪命中后的运行结果

## 下一步建议

优先继续做两件事：

1. **Starter / Demo Productization**
   - 增加具体示例 domain
   - 补“如何起一个新垂域 agent”的最小模板

2. **前端调试可视化**
   - 展示 runtime knowledge 命中信息
   - 展示 tool execution / cache / selected knowledge
   - 让这套框架更像真正可调试的 agent workbench
