# Framework Phase 27 实施记录

## 日期
2026-04-24

## 主题
主前端边界收口：Vue SPA 作为默认主入口，Legacy UI 降级为兼容层

## 背景
当前仓库同时存在两套前端：

- `frontend-vue/`：当前活跃的 Vue 3 + Vite 客户端
- `frontend/`：历史遗留的模板前端

这会带来几个典型问题：

1. 同一个问题容易在两套前端里重复修
2. 默认 server 入口不清晰，难以作为“通用 demo 框架”复用
3. 用户与开发者很难判断哪个前端才是主入口

因此这一阶段的目标不是删除 legacy UI，而是明确主次边界。

## 本次目标

1. 将 `frontend-vue` 提升为默认主前端
2. 保留 `frontend/` 作为兼容层，而不是继续作为默认 UI
3. 让 `agent_server` 的 UI 装配层显式表达这种边界

## 本次改动

### 1. 新增 UI 模式语义
- 文件：`backend/agent_server/config.py`

`AgentServerUIConfig` 新增：
- `mode: "spa" | "legacy" | "disabled"`
- `spa_dist_dir`
- `spa_assets_mount_path`
- `spa_route_paths`
- `legacy_mount_prefix`

默认 `full_stack` 现在使用：
- `mode="spa"`

也就是说，当前产品形态默认以 Vue SPA 作为主前端。

### 2. App Factory 支持 SPA 主入口
- 文件：`backend/agent_server/app.py`

新增：
- `_register_spa_ui()`
- `_register_ui()`

行为变化：

#### 当 `mode="spa"` 且 `frontend-vue/dist` 可用时
- `/`、`/login`、`/chat`、`/learnings`、`/skills`、`/settings`、`/search`
  统一返回 Vue SPA 的 `index.html`
- `/assets` 挂载到 `frontend-vue/dist/assets`
- `/index` 兼容重定向到 `/chat`
- legacy UI 仍保留，但只挂在：
  - `/legacy/login`
  - `/legacy/index`

#### 当 SPA 构建产物不存在时
- 自动回退到 legacy UI

这使默认装配更清晰，也保留了回退稳定性。

### 3. 对外导出更新
- 文件：`backend/agent_server/__init__.py`

新增导出：
- `AgentServerUiMode`

### 4. Demo 文档更新
- 文件：`docs/agent_framework_demo_guide.md`

明确说明：
- `frontend-vue` 是主前端
- `frontend/` 是兼容前端
- 新垂域 demo 应优先基于 Vue SPA

## 测试

### 更新
- `tests/agent_framework/test_agent_server_app.py`

新增覆盖：
- 默认 app factory 在 SPA 存在时暴露 Vue 主路由与 `/legacy/*` 兼容入口
- 显式提供一个临时 SPA dist 目录时，可稳定装配 SPA 主入口
- `learning_demo` / `api_only` / `embedded` 继续保持无 UI 或裁剪 UI 行为

## 验证结果
- `test_agent_server_app` 通过
- 完整后端测试：59 项通过

## 结果
这一步完成后，仓库的前端边界终于清晰了：

- `frontend-vue`：默认主前端
- `frontend/`：兼容层

这对于“做成可通用复用的 demo 框架”非常关键，因为它避免了未来每个新 agent demo 都在两套前端之间摇摆。

## 下一步建议

优先继续做两件事：

1. **知识治理继续增强**
   - 增加 scope / rollback / enabled
   - 记录 runtime knowledge 命中效果

2. **真正的 starter/demo 入口**
   - 增加示例 domain package
   - 补“如何创建新垂域 agent”的模板与脚手架说明
