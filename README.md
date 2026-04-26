# MyPrivateAgent Agent Framework Demo

## 项目定位
本仓库已从“单项目私有助手”演进为“可复用的通用智能体 Demo 框架”，用于后续垂域 Agent 快速孵化。

核心边界：
- 框架层：`backend/agent_framework`、`backend/agent_server`
- 业务层：`backend/services` 中领域服务、`frontend-vue` 页面与文案

## 当前状态（2026-04-24）
- 后端执行链：`AgentHarness + Orchestrator + ChatService` 已收口
- 前端主界面：`frontend-vue`（Vue SPA）为默认展示面
- 反馈闭环：消息级反馈、runtime effect 关联、feedback analytics 已打通
- 幂等治理：同用户同消息反馈采用 upsert 语义（避免统计污染）

## 快速启动

### 1. 后端
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
pip install -r requirements.txt
python scripts/doctor.py
python -m uvicorn main:app --reload --port 8000
```

### 2. 前端
```powershell
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm install
npm run dev
```

前端开发地址默认：`http://localhost:5173`  
后端 API 默认：`http://localhost:8000`

## 默认存储模式

当前 demo 默认使用：

- `SQLite` 本地存储
- 数据文件默认位于：`D:\AI\AIcode\MyPrivateAgent\.myagent\app.db`

这意味着：

- 演示和本地开发默认不需要额外安装 MySQL
- 会话、计划、反馈、artifact 等状态可直接本地持久化

如果后续要接入业务数据库，再显式配置：

```env
DB_MODE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=MyPrivateAgent
DB_USER=root
DB_PASSWORD=your_password
```

## 启动前自检与最小 Smoke

后端环境自检：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/doctor.py
```

最小后端 smoke 检查：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/smoke_check.py
```

认证 + 会话主链路 smoke：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/auth_session_smoke.py
```

聊天 SSE 主链路 smoke：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/chat_stream_smoke.py
```

聊天空响应兜底 smoke：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/chat_empty_response_smoke.py
```

聊天错误事件 smoke：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/chat_error_event_smoke.py
```

停止生成 smoke：
```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/chat_stop_generation_smoke.py
```

说明：
- `doctor.py` 会检查 `.env`、数据库连接、关键目录、前端构建产物、默认模型配置
- `smoke_check.py` 不会触发真实模型调用，只验证后端基础路由和健康检查是否可用
- `auth_session_smoke.py` 会验证游客登录、`/api/auth/me`、会话创建/列表/详情
- `chat_stream_smoke.py` 会验证聊天 SSE 能输出 `conversation_id`、流式内容、以及 `done` 结束事件
- `chat_empty_response_smoke.py` 会验证上游空响应时，后端仍会返回可展示的兜底回复和 `done`
- `chat_error_event_smoke.py` 会验证流式 `error` 事件能够被返回给前端展示链路
- `chat_stop_generation_smoke.py` 会验证停止生成链路的前端 store 合约与收尾行为
- 运行中的服务也可直接访问：`GET /api/health`

## Demo 入口
- 天气 Demo：`examples/weather_demo_app.py`
- 知识 Demo：`examples/knowledge_demo_app.py`

示例：
```powershell
cd D:\AI\AIcode\MyPrivateAgent
python -m uvicorn examples.weather_demo_app:app --port 8010
```

## 关键文档
- Starter 指南：`docs/agent_framework_starter_guide.md`
- Demo 指南：`docs/agent_framework_demo_guide.md`
- Demo 运行手册：`docs/demo_runbook.md`
- 测试手册：`docs/test_manual.md`
- Card Schema：`docs/agent_framework_card_schemas.md`
- 阶段记录索引：`问题记录/README.md`

## 维护命令

反馈重复数据清理（默认 dry-run）：
```powershell
cd D:\AI\AIcode\MyPrivateAgent
python backend/scripts/dedupe_message_feedback.py --preview-limit 20
```

执行清理：
```powershell
cd D:\AI\AIcode\MyPrivateAgent
python backend/scripts/dedupe_message_feedback.py --apply --limit-groups 50
```
