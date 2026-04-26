# Demo 运行与演示手册

## 1. 目标

这份手册面向当前项目的两类使用场景：

- 本地快速启动 demo
- 演示前做最小稳定性检查

当前项目已经调整为：

- 前端默认 `frontend-vue`
- 后端默认本地运行
- 存储默认 `SQLite`
- 外部 MySQL 改为可选模式

也就是说，**默认不需要额外安装 MySQL，就可以把 demo 跑起来。**

## 2. 默认运行模式

### 2.1 默认存储

当前 demo 默认使用：

- `DB_MODE=sqlite`
- 本地 SQLite 文件：`D:\AI\AIcode\MyPrivateAgent\.myagent\app.db`

特点：

- 无需额外数据库基础设施
- 适合 demo、本地开发、starter 框架复用
- 会话、计划、反馈、artifact 等状态可以本地持久化

### 2.2 默认前后端地址

- 后端 API：`http://localhost:8000`
- 前端开发地址：`http://localhost:5173`

## 3. 启动前提

### 3.1 后端

建议环境：

- Python 3.11
- 已安装 `backend/requirements.txt`

安装命令：

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
pip install -r requirements.txt
```

如果你之前已经在 `myenv` 里装过一轮失败或混乱的依赖，不建议直接在原环境上反复覆盖。更稳妥的做法是重建环境：

```powershell
conda create -n myenv python=3.11 -y
conda activate myenv
cd D:\AI\AIcode\MyPrivateAgent\backend
pip install -r requirements.txt
```

### 3.2 前端

建议环境：

- Node.js 18+
- npm 可用

安装命令：

```powershell
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm install
```

## 4. 标准启动顺序

### 4.1 启动后端

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
conda activate myenv
python scripts/doctor.py
python -m uvicorn main:app --reload --port 8000
```

说明：

- `doctor.py` 会先检查：
  - `.env`
  - 当前存储模式
  - SQLite/数据库连接
  - 关键目录
  - 前端构建产物
  - 默认模型配置

### 4.2 启动前端

```powershell
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm run dev
```

## 5. 演示前最小检查顺序

如果要演示，不建议直接打开页面就开始。建议先按下面顺序跑检查。

### 5.1 环境与基础接口

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/doctor.py
python scripts/smoke_check.py
```

### 5.2 认证与会话链路

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/auth_session_smoke.py
```

验证内容：

- 游客登录
- 获取当前用户
- 创建会话
- 会话列表
- 会话详情

### 5.3 聊天展示链路

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/chat_stream_smoke.py
python scripts/chat_empty_response_smoke.py
python scripts/chat_error_event_smoke.py
python scripts/chat_stop_generation_smoke.py
```

验证内容：

- 正常 SSE 流式输出
- `conversation_id`
- `done` 结束态
- 空响应兜底
- `error` 事件链路
- 停止生成链路

## 6. 前端回归检查

在改过前端聊天、Planner、MCP、设置页之后，建议至少执行：

```powershell
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm test
npm run build
```

当前这两条已经是 demo 可用性的最低回归门槛。

说明：

- `doctor.py` 只做环境与连接检查，不主动建表
- `auth_session_smoke.py` 和聊天相关 smoke 现在会自动初始化 demo 所需表结构

## 7. 建议演示顺序

如果你要向别人展示当前项目，建议按这个顺序：

1. 打开登录页，演示游客登录
2. 进入聊天页，发起一个普通问题
3. 演示 Planner 右侧面板
4. 演示设置页里的 MCP 管理面板
5. 演示 Skills 管理页
6. 如需说明稳定性，再展示 smoke 脚本和 `/api/health`

这样更像“一个通用 agent 平台 demo”，而不是单一聊天页。

## 8. 常见问题排查

### 8.1 `doctor.py` 报数据库连接失败

先看当前是不是默认 SQLite。

如果是默认模式：

- 检查 `.env` 是否把 `DB_MODE` 改成了 `mysql`
- 如果不需要 MySQL，删除或改回：

```env
DB_MODE=sqlite
```

### 8.2 前端能打开，但聊天一直没有结果

先执行：

```powershell
python scripts/chat_stream_smoke.py
python scripts/chat_empty_response_smoke.py
python scripts/chat_error_event_smoke.py
```

如果这些 smoke 都通过，再去看真实模型配置。

### 8.3 `pip install -r requirements.txt` 提示 `ResolutionImpossible`

当前项目使用的是 `langchain 0.3.x / langgraph 0.2.x` 这一代依赖栈，所以必须和 `langchain-openai 0.2.x` 配套，不能混用 `langchain-openai 1.x`。

如果你看到类似下面的冲突：

- `langchain 0.3.7 depends on langchain-core<0.4.0`
- `langchain-openai 1.1.13 depends on langchain-core>=1.2.29`

说明环境里用了错误的 OpenAI 适配包版本，或者旧环境里残留了冲突依赖。现在仓库已经修正为兼容组合：

- `langchain==0.3.7`
- `langchain-ollama==0.2.0`
- `langchain-openai==0.2.14`
- `langgraph==0.2.56`
- `openai==1.58.1`

建议直接重建环境并重装：

```powershell
conda deactivate
conda remove -n myenv --all -y
conda create -n myenv python=3.11 -y
conda activate myenv
cd D:\AI\AIcode\MyPrivateAgent\backend
pip install -r requirements.txt
```

如果安装完成后还出现这类提示：

- `langgraph-prebuilt 1.0.8 requires langchain-core>=1.0.0`

说明你当前激活的环境里还有旧版 `langgraph-prebuilt` 残留。这不是本项目当前依赖栈需要的包，清掉即可：

```powershell
pip uninstall -y langgraph-prebuilt langgraph-supervisor
pip install -r requirements.txt
```

另外，后端脚本建议始终从 `backend` 目录执行，例如：

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/doctor.py
```

### 8.4 前端一直处于“生成中”

当前已经有几层兜底：

- SSE `done` 正常结束
- 无 `done` 时 fallback done
- 空响应时 fallback content + done
- `error` 事件会立即收尾

如果仍出现问题，优先检查：

- 浏览器控制台
- 后端 `/api/chat` 返回流
- `frontend-vue/src/stores/conversation.js`

### 8.5 页面打不开，但后端正常

先确认：

```powershell
cd frontend-vue
npm run dev
```

如果是生产模式演示，再先执行：

```powershell
cd frontend-vue
npm run build
```

### 8.6 需要切回 MySQL

在 `.env` 显式设置：

```env
DB_MODE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=MyPrivateAgent
DB_USER=root
DB_PASSWORD=your_password
```

然后重新执行：

```powershell
cd backend
python scripts/doctor.py
python -m uvicorn main:app --reload --port 8000
```

## 9. 当前阶段的准确判断

当前项目：

- 作为 `demo / 通用智能体样板`：可以用
- 作为 `starter / 垂域框架基础`：可以复用
- 作为 `企业生产级正式系统`：还需要后续治理能力继续完善

当前最重要的是：

- 不再继续无节制扩功能
- 保持 demo 默认可运行
- 保持 smoke 脚本和前后端回归持续可用
- 按测试手册做固定顺序验收

## 10. 配套测试手册

- 统一测试手册：[test\_manual.md](./test_manual.md)
