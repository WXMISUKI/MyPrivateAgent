# MyPrivateAgent 测试手册

## 1. 目标

这份手册用于后续按固定顺序验证当前智能体 demo 的：

- 可启动性
- 前后端主链路可用性
- 聊天流式稳定性
- Planner / MCP / Skill 等框架能力的展示可用性
- 异常态与停止态是否能平稳收尾

建议每次合并前、对外演示前、以及重要重构后，都至少跑一遍这里的最小用例集。

## 2. 测试范围分层

### 2.1 L0 启动与环境层

目标：

- 能启动
- 默认 SQLite 模式可用
- 核心接口在线

### 2.2 L1 主链路层

目标：

- 登录
- 创建会话
- 发消息
- 流式返回
- 停止生成
- 空响应兜底
- 错误态收尾

### 2.3 L2 框架展示层

目标：

- Planner 可展示
- Tool Call 可展示
- MCP 管理页可展示
- Skill 管理页可展示

### 2.4 L3 回归层

目标：

- 前端自动化通过
- 关键后端 smoke 通过

## 3. 执行顺序

### 3.1 后端 smoke

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/doctor.py
python scripts/smoke_check.py
python scripts/auth_session_smoke.py
python scripts/chat_stream_smoke.py
python scripts/chat_empty_response_smoke.py
python scripts/chat_error_event_smoke.py
python scripts/chat_stop_generation_smoke.py
```

### 3.2 前端回归

```powershell
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm test
npm run build
```

## 4. 测试用例

### TC-001 启动自检

- 目标：确认 demo 默认环境可运行
- 前置条件：已安装 Python 依赖
- 步骤：运行 `python scripts/doctor.py`
- 预期结果：
  - 输出 `ok` 或等价通过状态
  - 显示当前为 `sqlite` 或本地默认模式
  - 无阻断级错误

### TC-002 基础健康检查

- 目标：确认后端基础路由可访问
- 前置条件：后端依赖已安装
- 步骤：运行 `python scripts/smoke_check.py`
- 预期结果：
  - 健康检查通过
  - 基础 API 可返回成功

### TC-003 游客登录与会话链路

- 目标：确认登录和会话基础能力可用
- 前置条件：后端可启动
- 步骤：运行 `python scripts/auth_session_smoke.py`
- 预期结果：
  - 游客登录成功
  - `/api/auth/me` 正常
  - 可创建会话
  - 会话列表和详情可返回

### TC-004 聊天正常流式输出

- 目标：确认 SSE 主链路可用
- 前置条件：后端可启动
- 步骤：运行 `python scripts/chat_stream_smoke.py`
- 预期结果：
  - 返回 `conversation_id`
  - 返回至少一段 `content`
  - 返回 `done`

### TC-005 聊天空响应兜底

- 目标：确认上游空响应不会让前端卡死
- 前置条件：后端可启动
- 步骤：运行 `python scripts/chat_empty_response_smoke.py`
- 预期结果：
  - 返回兜底文案
  - 最终返回 `done`

### TC-006 聊天错误事件收尾

- 目标：确认上游报错时链路可以正常收尾
- 前置条件：后端可启动
- 步骤：运行 `python scripts/chat_error_event_smoke.py`
- 预期结果：
  - 返回 `error` 事件
  - 前端展示链路不会永久停在生成中

### TC-007 停止生成

- 目标：确认“停止生成”按钮链路真实可用
- 前置条件：
  - 前端 `npm test` 环境可运行
  - 聊天页已打开
- 步骤：
  1. 发起一条会进入生成态的消息
  2. 点击消息上的“停止生成”
  3. 或运行 `python scripts/chat_stop_generation_smoke.py`
- 预期结果：
  - 当前请求被中断
  - assistant 消息结束生成态
  - 展示“已停止生成”或已生成片段
  - 页面不再保持 loading

### TC-008 前端最小自动化

- 目标：确认主界面关键行为未回归
- 前置条件：Node.js 环境可用
- 步骤：运行 `npm test`
- 预期结果：
  - 所有测试通过
  - 至少覆盖：
    - 消息流式渲染
    - 命令面板
    - 反馈提交
    - 停止生成

### TC-009 前端生产构建

- 目标：确认前端可产出构建包
- 前置条件：Node.js 环境可用
- 步骤：运行 `npm run build`
- 预期结果：
  - 构建成功
  - 无阻断级错误

### TC-010 Planner 展示

- 目标：确认 Todo/Planner 面板可展示
- 前置条件：前后端已启动
- 步骤：
  1. 进入聊天页
  2. 输入目标
  3. 点击“为当前目标生成计划”
- 预期结果：
  - 右侧出现计划
  - 计划项状态可切换
  - 时间线 / run trace 可展示

### TC-011 MCP 管理面板

- 目标：确认 MCP 管理入口可用
- 前置条件：前后端已启动
- 步骤：
  1. 打开设置页
  2. 查看 MCP server 列表
  3. 尝试新增或探测一个 server
- 预期结果：
  - 页面正常渲染
  - 列表、catalog、probe/handshake 按钮可操作

### TC-012 Skill 管理页

- 目标：确认 Skill 资产管理页可展示
- 前置条件：前后端已启动
- 步骤：
  1. 打开 Skill 管理页
  2. 查看已存在技能
  3. 尝试执行启停或读取
- 预期结果：
  - 页面正常渲染
  - 基本管理动作可用

## 5. 建议验收顺序

建议按下面顺序做人工验收：

1. `TC-001 ~ TC-003`
2. `TC-004 ~ TC-007`
3. `TC-008 ~ TC-009`
4. `TC-010 ~ TC-012`

## 6. 结果记录模板

每次测试可按下面模板记录：

```md
测试日期：
测试人：
版本/分支：

- TC-001：通过 / 失败
- TC-002：通过 / 失败
- TC-003：通过 / 失败
- TC-004：通过 / 失败
- TC-005：通过 / 失败
- TC-006：通过 / 失败
- TC-007：通过 / 失败
- TC-008：通过 / 失败
- TC-009：通过 / 失败
- TC-010：通过 / 失败
- TC-011：通过 / 失败
- TC-012：通过 / 失败

问题记录：
- 
```
