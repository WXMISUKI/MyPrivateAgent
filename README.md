# MyPrivateAgent

## 项目定位
本仓库当前定位为企业级 **Agent Runtime Control Plane**。它不是单一聊天 Demo，也不是某个外部 Agent 框架的替代实现；它负责 Runtime Core、ToolRuntime、Query Control、Governance Timeline、审批、审计、权限、外部 provider 边界和业务系统集成语义。

建议先读：

- 当前入口：`docs/architecture/agent_runtime_control_plane_entrypoint.md`
- 当前事实：`docs/architecture/current_architecture.md`
- 运行时契约：`docs/architecture/runtime_contracts.md`
- 扩展点：`docs/architecture/extension_points.md`
- 接入清单：`docs/guides/project_entrypoint_checklist.md`

## 当前状态

- Runtime Core 已具备 run/event/approval/trace/audit/artifact 的核心边界。
- Capability Layer 已具备 Tool / MCP / Skill / Memory / Command / provider contract。
- Governance Layer 已具备 runtime contract gate、doctor、health、timeline 和 quality gate evidence。
- Embedded SDK / Agent Harness Facade 已具备最小开发者入口，但仍处于持续硬化阶段。
- Domain agent 线已具备 catalog、capability linkage、grounded-answer trial/package/composition 和 repo-side smoke trial pack。
- 默认 `/api/chat` retrieval injection 仍保持关闭；外部 RAG/GraphRAG/OCR/Voice 等重能力保持 provider-first。

## 快速启动

### 1. 后端
```powershell
conda activate myenv
cd D:\AI\AIcode\MyPrivateAgent
pip install -r backend\requirements.txt
python backend\scripts\doctor.py
python -m uvicorn backend.main:app --reload --port 8000
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
- `AUTH_MODE=demo_guest` 免登录演示模式
- 数据文件默认位于：`D:\AI\AIcode\MyPrivateAgent\.myagent\app.db`

这意味着：

- 演示和本地开发默认不需要额外安装 MySQL
- 前端默认不会阻塞在登录页，会自动使用 guest 身份进入聊天
- 会话、计划、反馈、artifact 等状态可直接本地持久化

## 通用智能体运行时约定

当前框架已经补上两层通用底座能力：

- `Agent Identity`：主智能体会以“通用协调智能体”的身份运行，而不是裸模型直出
- `Capability Profile`：每轮会汇总当前工具、Skill、MCP capability，并据此判断能做什么、不能做什么、缺什么能力
- `Layered Agent Memory`：主智能体支持按层加载 `GLOBAL_AGENT.md / PROJECT_AGENT.md / PROJECT_AGENT.local.md`，用于沉淀长期规则层

这意味着后续做垂域智能体时，重点不再是反复改主执行链，而是：

- 补工具层
- 补 Skill 层
- 补 MCP capability

框架会尽量基于现有能力给出：

- 已完成部分
- 当前缺口
- 建议补强能力

当触发能力边界降级时，对应事件也会写入 run trace，方便后续统计：

- 当前最常缺什么能力
- 更适合补工具、Skill，还是补 MCP

## 模型与 Provider 配置

前端模型下拉不再写死，默认从后端动态获取 `/api/models`。

当前已支持：

- `volcengine-ark`（豆包 / Ark 兼容模型）
- `ollama`（本地模型，优先探测已安装模型）

运行时能力面还支持通过 `/api/runtime-profile` 读取当前：

- `auth_mode`
- `default_model`
- provider 列表
- model 目录

并通过 `PATCH /api/runtime-profile` 持久化修改 demo 安全配置项：

- `auth_mode`
- `default_model`

配置会写入本地：

- `.myagent/runtime_surface.json`

同时可通过 `/api/capability-gaps` 聚合查看近期能力缺口：

- 高频缺失能力类型
- 建议补强方向
- 近期典型案例

关键配置：

```env
DEFAULT_MODEL=doubao
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=your_key
ARK_MODEL=doubao-seed-2-0-mini-260215
ARK_MODEL_ALIAS=doubao
ARK_MODEL_DISPLAY_NAME=豆包 (火山引擎)
ARK_EXTRA_MODELS=
OLLAMA_BASE_URL=http://localhost:11434
AUTH_MODE=demo_guest
```

其中 `ARK_EXTRA_MODELS` 支持按别名追加更多 Ark 模型，格式为：

```env
ARK_EXTRA_MODELS=ark-pro=doubao-pro-32k|豆包 Pro|false,ark-reasoner=deepseek-r1|推理模型|true
```

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
- 当前入口：`docs/architecture/agent_runtime_control_plane_entrypoint.md`
- 接入清单：`docs/guides/project_entrypoint_checklist.md`
- 当前架构：`docs/architecture/current_architecture.md`
- 运行时契约：`docs/architecture/runtime_contracts.md`
- 扩展点：`docs/architecture/extension_points.md`
- Starter 指南：`docs/agent_framework_starter_guide.md`
- Demo 指南：`docs/agent_framework_demo_guide.md`
- Demo 运行手册：`docs/demo_runbook.md`
- v0 冻结验收模板：`docs/v0_freeze_acceptance_report_template.md`
- 通用框架实施清单：`docs/framework_execution_roadmap.md`
- Claude 对齐完善方案：`docs/claude_alignment_improvement_plan.md`
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
