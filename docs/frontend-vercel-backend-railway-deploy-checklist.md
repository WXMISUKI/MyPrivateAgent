# Frontend(Vercel) + Backend(Railway) 部署检查清单

## 1. Vercel 环境变量
- `VITE_API_BASE_URL`: `https://<your-railway-domain>/api`
- 请在 `Production`、`Preview`、`Development` 三个环境分别配置。

## 2. 运行时配置（推荐）
- 文件：`frontend-vue/public/app-config.js`
- 可在部署阶段注入：
  - `window.__APP_CONFIG__.apiBaseUrl = "https://<your-railway-domain>/api"`
- 优先级高于 `VITE_API_BASE_URL`，用于紧急切换后端地址而不重新打包前端。

## 3. 线上验证
- 打开浏览器控制台，确认请求目标为 Railway 域名而不是 `https://<vercel-domain>/api/...`。
- 在 Vercel Deployments 的 Build Logs 中检查是否读取了 `VITE_API_BASE_URL`。
- 确认当前部署 commit 与本地预期 commit 一致。

## 4. 后端联调检查
- Railway 后端允许来自 Vercel 域名的 CORS。
- `/api/*` 路由可正常响应 `OPTIONS` 预检请求。
- 关键接口自检：`/api/models`、`/api/auth/me`、`/api/chat`。
