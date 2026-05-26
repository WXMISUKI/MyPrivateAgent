# MyPrivateAgent Vercel 一体化部署方案

## 1. 目标

- 前后端部署到同一个 Vercel 项目
- 前端静态资源由 Vercel CDN 托管
- 后端通过轻量 FastAPI Serverless 提供 `/api/*`
- 线上默认使用内存态存储，不依赖数据库
- 不适合 Vercel 的本地文件写入和本地进程能力显式降级

## 2. 当前实现

- 根目录 `vercel.json` 负责统一部署编排
- 根目录 `api/index.py` 作为 Vercel Python 入口，运行轻量 `api/vercel_app.py`
- `frontend-vue/dist` 作为前端构建输出目录
- 前端线上默认请求同域 `/api`
- Vercel 环境默认 `DB_MODE=memory`
- 完整 LangChain/LangGraph/MCP/技能运行时仍由本地或 Docker 后端承载；Vercel 免费部署保留登录、模型目录和基础聊天演示能力

## 3. 部署步骤

1. 在 Vercel 导入当前仓库
2. Root Directory 选择仓库根目录
3. Framework Preset 选择 `Other`
4. Build Command 使用仓库内 `vercel.json` 配置
5. Output Directory 使用仓库内 `vercel.json` 配置
6. 确认 Vercel 项目中没有配置 `VITE_API_BASE_URL` 指向 Railway；一体化部署应让前端默认请求同域 `/api`

## 4. 环境变量

至少配置：

```env
SECRET_KEY=请设置强随机值
DEFAULT_MODEL=doubao
ARK_API_KEY=你的火山引擎 Key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=你的模型或接入点
AUTH_MODE=demo_guest
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://你的-vercel-域名
CORS_ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
```

Python 版本由根目录 `.python-version` 与 `pyproject.toml` 约束为 `3.12.*`，避免 Vercel 选择更新 Python 版本时触发 PyO3/Rust 扩展依赖兼容问题。

建议不要在 Vercel 上配置：

- `DB_MODE=mysql`
- `DB_MODE=sqlite`
- 任意本地地址形式的服务 URL

## 5. Vercel 运行时约束

### 已兼容

- 游客模式登录
- 基础对话
- 会话与消息的进程内临时存储
- Provider 读取与测试
- 远程 `http` 型 MCP

### 已降级

- Skill 导入
- Skill 删除
- Skill AI 创建
- 本地 `stdio` 型 MCP

### 当前限制

- 所有会话数据为内存态，函数实例重启后会丢失
- Runtime profile 覆盖配置与 provider 覆盖配置仅在当前实例内有效
- 不适合作为强状态生产系统

## 6. 验证清单

部署完成后验证：

1. 打开首页，确认前端正常加载
2. 打开浏览器网络面板，确认接口请求为同域 `/api/*`
3. 访问 `/api/health/live` 返回 `status=ok`
4. 访问 `/api/health` 返回 `status=ok` 或 `warn`
5. 游客模式可进入 `/chat`
6. 可以发起至少一轮对话
7. Skills 页面显示 Vercel 只读提示
8. MCP 页面可新增 `http` 型远程服务，`stdio` 型服务会被拒绝

## 7. 后续建议

如后续需要正式生产化，建议按顺序升级：

1. 将会话和治理数据迁移到外部数据库
2. 将 Skills 资产迁移到对象存储
3. 将运行时配置迁移到外部配置中心
4. 将后台治理和长耗时任务迁移到独立 Worker
