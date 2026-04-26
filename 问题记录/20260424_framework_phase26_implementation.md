# Framework Phase 26 实施记录

## 日期
2026-04-24

## 主题
Runtime Knowledge 治理分级与 `learning_demo` Demo Preset

## 背景
Phase 25 已经把 `SystemPrompt` 与 `BestPractice` 接入 runtime 主链，但当时仍存在两个明显问题：

1. 注入策略过于“全量”，缺少治理层，不像成熟 harness 的知识注入策略
2. 框架虽然已有 `full_stack / api_only / embedded` preset，但还缺少面向“自学习调优”场景的 demo 装配入口

## 本次目标

1. 给 runtime knowledge 增加最小治理分级
2. 增加一个更明确的通用 demo preset，方便后续做可复用演示与垂域套用

## 本次改动

### 1. Runtime Knowledge 分级治理
- 文件：`backend/services/runtime_learning_service.py`

新增 `RuntimeKnowledgeLevel`：
- `diagnostic`
- `advisory`
- `enforced`

当前治理规则：

#### SystemPrompt
- `tags` 含 `diagnostic` => `diagnostic`
- `tags` 含 `enforced` => `enforced`
- `prompt_type in {"tool_usage", "workflow"}` 或 `priority >= 5` => `enforced`
- 其他 => `advisory`

#### BestPractice
- `tags` 含 `diagnostic` => `diagnostic`
- `tags` 含 `enforced` 或优先级 `high/critical` => `enforced`
- 其他 => `advisory`

#### 注入行为
- `enforced` 和 `advisory` 会进入 system prompt
- `diagnostic` 只记录在 metadata 中，不注入模型

这让运行时知识开始具备“治理意识”，不再是简单拼接。

### 2. Runtime metadata 增强
`RuntimeKnowledgeContext.metadata` 新增：
- `governance`
- `enforced_count`
- `advisory_count`
- `diagnostic_count`

这样后续前端调试视图、artifact 复盘和效果分析都能直接消费治理信息。

### 3. 新增 `learning_demo` server preset
- 文件：`backend/agent_server/config.py`
- 文件：`backend/agent_server/__init__.py`

新增：
- `LEARNING_DEMO_ROUTE_GROUPS`
- `PRESET_LEARNING_DEMO`

特点：
- 关闭 legacy UI
- 保留：
  - `auth`
  - `core`
  - `learning`
  - `permissions`
- 不挂 `skills` / `admin`

这个 preset 更适合：
- 演示 runtime knowledge 注入
- 自学习系统验证
- 新垂域 agent 的最小 demo 骨架

### 4. 补 demo guide
- 文件：`docs/agent_framework_demo_guide.md`

补充内容：
- 当前框架的可复用边界
- 现有 server preset 说明
- runtime knowledge governance 说明
- 如何基于它做一个新垂域 agent

## 测试

### 新增/更新
- `tests/agent_framework/test_runtime_learning_service.py`
- `tests/agent_framework/test_agent_server_app.py`

覆盖内容：
- `diagnostic` 知识不会进入 system prompt
- `enforced` 知识会进入 runtime 注入
- `learning_demo` preset 装配行为正确

## 验证结果
- 定向测试：16 项通过
- 完整后端测试：58 项通过

## 结果
这一步之后，项目离“成熟 harness 风格的可复用 demo 框架”又近了一层：

- runtime knowledge 不再只是简单拼接
- framework 开始有面向学习/调优场景的独立 demo preset
- 文档和装配入口更接近可复用产品形态

## 下一步建议

优先继续做两件事：

1. **统一主前端**
   - 明确 `frontend-vue` 为单一主入口
   - 将 legacy `frontend/` 降级为兼容层或移除

2. **知识治理继续增强**
   - 增加 scope / rollback / enabled 策略
   - 记录“本次运行命中了哪些知识，效果如何”
   - 为知识注入增加更明确的评估入口
