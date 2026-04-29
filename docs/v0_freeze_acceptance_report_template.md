# v0 冻结验收报告模板（通用智能体框架 Demo）

## 1. 基本信息

- 验收版本：`v0`
- 验收日期：`YYYY-MM-DD`
- 验收环境：
  - OS：
  - Python：
  - Node.js：
  - 前端地址：
  - 后端地址：
- 验收人：

---

## 2. 冻结范围

本次 `v0` 冻结范围仅包含：

- 通用执行链（意图识别 -> 计划 -> 工具调用 -> 结果消费 -> 完成度评估 -> 最终答复）
- 能力边界反馈链路（`capability_gap_fallback`）
- 运行时能力面与治理面板（含门禁、整改状态、建议分派）
- demo 模式降级能力（前端本地缓存/本地状态映射）

不包含：

- 垂域业务工具实现
- 企业级权限与审计全量能力
- 生产级高可用与多租户治理

---

## 3. 验收清单（勾选）

### 3.1 启动与基础健康

- [ ] 后端 `python scripts/doctor.py` 通过（或输出可解释告警）
- [ ] 后端 `python scripts/smoke_check.py` 通过
- [ ] `GET /api/health` 正常
- [ ] `GET /api/models` 正常

### 3.2 认证与会话链路（demo_guest）

- [ ] `python scripts/auth_session_smoke.py` 通过
- [ ] 游客登录正常
- [ ] 会话创建、列表、详情正常

### 3.3 聊天与流式收尾链路

- [ ] `python scripts/chat_stream_smoke.py` 通过
- [ ] `python scripts/chat_empty_response_smoke.py` 通过
- [ ] `python scripts/chat_error_event_smoke.py` 通过
- [ ] `python scripts/chat_stop_generation_smoke.py` 通过
- [ ] 复合任务下能输出“已完成/当前缺口/建议补强能力”

### 3.4 治理看板与门禁

- [ ] `/api/capability-gaps` 可返回摘要
- [ ] 看板可显示 remediation_targets 与状态
- [ ] 可进行单条与批量状态更新
- [ ] `doctor --capability-gaps` 可输出 `pending_actions/remediation_targets`
- [ ] CI 门禁命令可运行并返回预期退出码

### 3.5 Demo 无数据库依赖降级

- [ ] 后端不可用时看板可加载本地缓存摘要
- [ ] 状态更新失败可降级到本地状态映射
- [ ] 批量操作审计本地可见并可清空

### 3.6 前端回归

- [ ] `npm test` 通过
- [ ] `npm run build` 通过

---

## 4. 门禁结果记录

### 4.1 命令

```powershell
python backend/scripts/doctor.py --capability-gaps --window-days 14 --limit 200 --max-open-actions 10 --max-long-blocked-actions 0
```

### 4.2 结果摘要

- `gate_passed`：
- `benchmark_gate_passed`：
- `non_closed_action_count`：
- `long_blocked_action_count`：
- `open_action_gate_breached`：
- `long_blocked_action_gate_breached`：

---

## 5. 已知问题与豁免

| 编号 | 现象 | 影响范围 | 临时策略 | 计划修复版本 | 负责人 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

---

## 6. 结论

- 冻结结论：
  - [ ] 通过（可作为通用智能体框架 demo 基线）
  - [ ] 有条件通过（需跟踪“已知问题与豁免”）
  - [ ] 不通过（需继续整改）

- 结论说明：

---

## 7. 后续动作（进入垂域前）

- [ ] 冻结 `v0` 分支/Tag
- [ ] 确认 roadmap 下一阶段范围（不在 `v0` 热修中扩功能）
- [ ] 输出垂域接入清单（工具层/Skill 层/MCP 层）

