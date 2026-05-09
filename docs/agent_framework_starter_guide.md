# Agent Framework 起步指南

## 目的

当你准备基于当前框架创建新的垂域 Agent 时，请使用本指南，而不是直接复制产品级行为。

## 推荐起点

先选择最接近目标形态的 preset：

- `weather_demo`
  - 重点：确定性工具、实时查询、结构化卡片
  - 路由分组：`auth`、`core`、`permissions`
- `knowledge_demo`
  - 重点：运行时知识注入、learnings、治理
  - 路由分组：`auth`、`core`、`learning`、`permissions`
- `learning_demo`
  - 重点：不依赖完整产品外壳的运行时知识实验
- `api_only`
  - 重点：不带 UI 的后端集成

## 示例入口

- [weather_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/weather_demo_app.py)
- [knowledge_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/knowledge_demo_app.py)

运行示例：

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python -m uvicorn examples.weather_demo_app:app --port 8010
```

如果是知识型 starter：

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python -m uvicorn examples.knowledge_demo_app:app --port 8011
```

## 构建新的垂域 Agent

1. 先选一个与目标形态接近的 preset。
2. 添加垂域工具与 `ToolSpec`。
3. 只有在确定性输出确实值得结构化展示时，才补充垂域卡片 schema。
4. 通过 learnings API 或 seed data 注入垂域 Prompt / 最佳实践。
5. 将垂域逻辑放在专门的 service 中，而不是直接修改运行时核心。
6. 如果需要可评估的 Agent 行为，应把用户反馈回接到 runtime effect review，而不是只记录聊天日志。

## 最小垂域清单

- 工具层：
  - 定义工具
  - 定义 `ToolSpec`
  - 定义权限级别
  - 如果结果可确定，定义缓存策略
- 输出层：
  - 决定使用 `plain_text` 还是 `structured_card`
  - 只有在可复用时才新增卡片 schema
- 知识层：
  - 决定哪些 prompts 是 `enforced`
  - 决定作用域标签，例如 `scope:chat`
  - 显式标记回滚项
- 反馈层：
  - 为 assistant 消息提供反馈 API
  - 确保流式 `done` 事件包含已持久化的 assistant `message_id`
  - 强制消息级反馈幂等（同一用户 + 同一消息 => 更新，而不是重复插入）
  - 将反馈关联到 `runtime_knowledge_effect`
  - 将重复的负反馈转成可审核的 learnings
  - 提供反馈分析接口（`scope / prompt_key / practice_id`）用于治理
- Demo 层：
  - 增加一个示例 app 入口
  - 记录预期路由与依赖服务

## 反馈数据维护

先使用 dry-run：

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python backend/scripts/dedupe_message_feedback.py --preview-limit 20
```

分批执行清理：

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python backend/scripts/dedupe_message_feedback.py --apply --limit-groups 50
```

## 当前复用规则

以下部分视为框架代码：

- `backend/agent_framework`
- `backend/agent_server`
- 共享运行时服务

以下部分视为垂域 / 应用代码：

- 天气服务
- 垂域 Prompt
- 垂域 Practices
- 产品特定页面与文案
