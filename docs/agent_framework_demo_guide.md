# Agent Framework Demo 指南

## 目标

当前仓库已经包含两层可复用能力：

- `backend/agent_framework`：可复用的运行时基础原语
- `backend/agent_server`：可复用的 FastAPI Server 组装层

当前应用仍然是 `MyPrivateAgent`，但代码库已经可以作为新垂域 Agent 的演示框架复用。

## 推荐复用边界

以下部分建议直接复用：

- 运行时状态、事件、工具元数据、artifacts、缓存
- Server app factory、auth provider、router registry、HTTP/SSE 辅助层
- 结构化卡片协议与前端卡片注册表

需要保持隔离的垂域代码包括：

- 天气服务
- 垂域 Prompt
- 垂域工具
- 垂域卡片 schema

## 前端边界

`frontend-vue` 现在是该可复用 Demo 框架的主客户端界面。

- 默认 `full_stack` 模式会直接托管 `frontend-vue/dist` 构建后的 Vue SPA
- 旧的模板式前端已不再作为默认 Demo 的一部分
- 新的垂域 Demo 应只面向 `frontend-vue` 开发

## 当前 Server 预设

- `full_stack`：当前产品形态，主界面为 Vue SPA
- `api_only`：无旧 UI、偏 API 集成的部署模式
- `embedded`：轻量嵌入模式
- `learning_demo`：聊天 + learnings + permissions 的演示预设，适合运行时知识实验
- `weather_demo`：偏天气 / 实时查询的起步预设
- `knowledge_demo`：偏知识与 learnings 的起步预设

示例：

```python
from backend.agent_server import create_app

app = create_app(preset="learning_demo")
```

起步型示例可参考：

- [agent_framework_starter_guide.md](D:/AI/AIcode/MyPrivateAgent/docs/agent_framework_starter_guide.md)
- [weather_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/weather_demo_app.py)
- [knowledge_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/knowledge_demo_app.py)

## 运行时知识治理

当前运行时知识通过 `RuntimeLearningService` 注入。

支持的治理等级：

- `enforced`：作为强约束运行时规则注入
- `advisory`：作为建议性信息注入
- `diagnostic`：仅记录在元数据中，不注入模型

当前分类规则刻意保持简单：

- `SystemPrompt.tags` 包含 `enforced` => `enforced`
- `SystemPrompt.tags` 包含 `diagnostic` => `diagnostic`
- `prompt_type in {"tool_usage", "workflow"}` 或 `priority >= 5` => `enforced`
- 高优先级 `BestPractice` => `enforced`
- 带 `diagnostic` 标签的 practices => `diagnostic`

## 如何构建新的垂域 Agent

1. 添加垂域工具和对应 `ToolSpec`
2. 如果确定性输出需要结构化渲染，再补充垂域卡片 schema
3. 通过 learnings API 或 seed data 注入垂域 Prompt / 最佳实践
4. 选择一个预设：
   - `api_only` 适合后端集成
   - `learning_demo` 适合迭代式运行时调优
5. 通过增加小型垂域 service layer 扩展能力，而不是直接修改运行时核心

## 推荐下一步

- 继续把 `frontend-vue` 保持为唯一主客户端
- 为新的垂域 Agent 增加 starter templates
- 补充 `tool_result -> done -> structured_card` 的端到端测试
- 增加运行时知识的回滚与作用域控制
