# MyPrivateAgent 线上部署 CORS 问题修复指南

## 1. 问题背景
- 前端部署在 Vercel，后端部署在 Railway。
- 前端请求已正确指向 Railway（不再是 `vercel.app/api/...`）。
- 浏览器仍报错：
  - `No 'Access-Control-Allow-Origin' header is present`
  - `Response to preflight request doesn't pass access control check`

## 2. 根因分析
这次问题由两个阶段叠加导致：

1. 前端阶段
- 历史实现中 `API_BASE_URL` 有被构建期固化为 `"/api"` 的风险，导致请求落到前端域名。
- 已通过运行时解析配置修复（统一 `buildApiUrl/getApiBaseUrl`）。

2. 后端阶段（核心）
- `Origin` 请求头可达后端，但部分部署 preset 使用了默认 CORS 配置（仅 localhost），与生产配置不一致。
- 结果是：后端未返回 `Access-Control-Allow-Origin`，浏览器拦截跨域请求。

## 3. 最终修复方案

### 3.1 前端修复（已完成）
- 统一 API 基址解析层，支持：
  - `window.__APP_CONFIG__.apiBaseUrl`（运行时）
  - `VITE_API_BASE_URL`（构建期）
  - 环境兜底策略
- 全量替换 `'/api'` 直写请求，避免绕过统一配置。

### 3.2 后端修复（已完成）
- 在 `backend/agent_server/app.py` 使用统一 CORS 中间件逻辑：
  - 对命中白名单或正则的 `Origin` 返回：
    - `Access-Control-Allow-Origin`
    - `Access-Control-Allow-Credentials`
    - `Access-Control-Allow-Methods`
    - `Access-Control-Allow-Headers`
    - `Access-Control-Max-Age`
    - `Vary: Origin`
  - 对预检请求 `OPTIONS` 返回 `204` 并补齐 CORS 头。
- 在 `backend/agent_server/config.py` 统一所有 preset 的 CORS 读取来源，避免 `full_stack` 与 `api_only` 等模式不一致。
- 在 `backend/config.py` 增加配置清洗：
  - 自动去除引号
  - 去除尾部 `/`

## 4. Railway 环境变量模板
- `CORS_ALLOWED_ORIGINS`
  - `https://my-private-agent.vercel.app,http://localhost:5173,http://localhost:8000`
- `CORS_ALLOWED_ORIGIN_REGEX`
  - `https://.*\.vercel\.app`

说明：
- 生产域名用 `CORS_ALLOWED_ORIGINS` 精确匹配。
- Preview 域名建议用正则匹配。

## 5. 验证步骤（发布后必做）

1. 验证普通跨域请求
```bash
curl -i "https://myprivateagent-backend-production.up.railway.app/api/models" \
  -H "Origin: https://my-private-agent.vercel.app"
```
期望响应头包含：
- `Access-Control-Allow-Origin: https://my-private-agent.vercel.app`
- `Access-Control-Allow-Credentials: true`

2. 验证预检请求
```bash
curl -i -X OPTIONS "https://myprivateagent-backend-production.up.railway.app/api/chat" \
  -H "Origin: https://my-private-agent.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization"
```
期望：
- 状态码 `204`
- 返回完整 `Access-Control-Allow-*` 头

3. 前端联调验证
- 在 Vercel 页面刷新后发起登录和聊天。
- 浏览器控制台不再出现 CORS 相关报错。

## 6. 回归风险与规避
- 风险：更换部署 preset 后 CORS 行为回退。
  - 规避：所有 preset 已统一读同一套 CORS 配置。
- 风险：运维平台环境变量写法错误（引号、尾斜杠）。
  - 规避：后端已做配置清洗，但仍建议按模板填写。
- 风险：新增跨域域名未同步 CORS 白名单。
  - 规避：发布流程加入“域名变更即更新 CORS 配置”检查项。

## 7. 建议的发布检查清单
- Vercel：
  - `VITE_API_BASE_URL` 已配置到 Production/Preview/Development。
  - 若启用运行时注入，`public/app-config.js` 结果正确。
- Railway：
  - `CORS_ALLOWED_ORIGINS`、`CORS_ALLOWED_ORIGIN_REGEX` 已配置。
  - 服务已使用最新 commit 重新部署。
- 端到端：
  - `runtime-profile`、`auth/guest`、`models`、`chat` 全链路可用。
