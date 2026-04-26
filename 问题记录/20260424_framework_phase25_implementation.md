# Framework Phase 25 实施记录

## 日期
2026-04-24

## 主题
自学习系统接入 Runtime 主链的最小闭环

## 背景
当前仓库已经具备：

- 学习记录：`Learning`
- 最佳实践：`BestPractice`
- 系统提示：`SystemPrompt`
- 自动审核与知识转化

但这些能力此前主要停留在后台管理和治理层，并没有稳定回流到 agent 运行时。  
这意味着“自学习系统”更像知识管理系统，而不是成熟 harness 常见的 runtime improvement loop。

## 本次目标
先做最小闭环，而不是一次性做复杂治理：

1. 读取已启用 `SystemPrompt`
2. 读取有限条 `BestPractice`
3. 在每次运行开始前注入到 runtime system prompt
4. 将本次命中的知识快照写入 artifact，便于复盘

## 本次改动

### 1. 新增 Runtime Learning Service
- 文件：`backend/services/runtime_learning_service.py`

新增：
- `RuntimeKnowledgeContext`
- `RuntimeLearningService`
- `get_runtime_learning_service()`

职责：
- 读取 active `SystemPrompt`
- 读取高优先级 `BestPractice`
- 组装成一段运行时 system prompt
- 输出可追踪的 metadata：
  - `prompt_keys`
  - `practice_ids`
  - `prompt_count`
  - `practice_count`

### 2. 编排层注入 runtime knowledge
- 文件：`backend/orchestrator.py`

修改后：
- 每次 `process_message()` 开始时都会生成 `runtime_knowledge`
- 若存在知识内容，则在消息列表前插入 `SystemMessage`
- 这样 `AgentHarness` 会在主执行链里直接消费这部分知识

这是本阶段最关键的变化，意味着自学习信息第一次稳定进入了 runtime 主链。

### 3. 知识注入快照 artifact 化
- 文件：`backend/services/orchestrator_service.py`

新增：
- `persist_runtime_knowledge_artifact()`

效果：
- 每次实际注入的 runtime knowledge 会以 `runtime_knowledge` artifact 持久化
- 后续可用于：
  - 排查这次运行到底用了哪些知识
  - 做知识命中效果复盘
  - 给未来的调试 UI / 审计 UI 提供数据

### 4. CI 与测试补齐
- 文件：`.github/workflows/ci.yml`
- 新增测试：`tests/agent_framework/test_runtime_learning_service.py`
- 更新测试：`tests/agent_framework/test_orchestrator_service.py`

覆盖内容：
- runtime knowledge context 生成
- 空知识场景
- `runtime_knowledge` artifact 落库/落内存

## 验证结果
- 定向回归：7 项通过
- 完整后端测试：56 项通过

## 当前意义
这一步完成后，项目的“自学习系统”首次具备了最小 runtime 闭环：

`Learning / Prompt / Practice -> RuntimeKnowledge -> SystemMessage Injection -> Artifact Trace`

虽然还没有做到：
- 按效果评估自动晋升
- 按域/任务动态选择知识
- 知识回滚与 A/B 对比

但已经从“后台记录系统”提升到了“运行时可用系统”。

## 下一步建议
建议继续分两段推进：

1. **知识治理增强**
   - 区分 `diagnostic / advisory / enforced`
   - 增加 enabled / scope / rollback 字段
   - 只让经过治理的知识进入 runtime

2. **demo framework 收口**
   - 明确单一主前端
   - 增加 starter/demo 文档
   - 让新垂域 agent 能基于 preset + tool + knowledge provider 快速装配
