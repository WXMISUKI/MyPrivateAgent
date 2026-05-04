# Failover 告警可观测性说明（单机 Demo）

## 1. 目标
- 让运维/演示人员在 `Settings` 和 `Chat` 两个入口快速识别 Provider failover 风险。
- 提供统一的阈值、告警等级和刷新策略，保证前后端口径一致。

## 2. 后端数据契约
- `GET /api/runtime-profile`
  - 顶层字段：`failover_thresholds`
  - 结构：
    - `medium`: `float`，默认 `0.2`
    - `high`: `float`，默认 `0.4`
- `PATCH /api/runtime-profile`
  - 支持更新：
    - `failover_thresholds.medium`
    - `failover_thresholds.high`
  - 校验规则：
    - `(0, 1)` 区间
    - `high > medium`
- `GET /api/health`
  - `failover` 节点新增：
    - `alert_thresholds`: `{ medium, high }`
    - `alert_level`: `low | medium | high`
  - `alert_level` 计算：
    - `switch_rate > high` => `high`
    - `switch_rate > medium` => `medium`
    - 其他 => `low`

## 3. 前端展示策略
- `SettingsView`
  - 展示 failover 统计看板、阈值配置、健康告警等级、最后更新时间。
  - 阈值保存后：
    - 本地 `settings` store 持久化（兜底）
    - 同步 `PATCH /api/runtime-profile`（权威）
- `ChatView`
  - 当 `alert_level` 为 `medium/high` 时显示顶部横幅。
  - 当 `muteHealthAlerts=true` 时不显示横幅（只在设置页查看）。

## 4. 刷新与性能
- `SettingsView` 与 `ChatView` 均采用 60 秒轮询 `GET /api/health`。
- 组件卸载时清理轮询定时器，避免内存泄漏。

## 5. 本地配置项
- `frontend-vue/src/stores/settings.js`
  - `failoverMediumThreshold`
  - `failoverHighThreshold`
  - `muteHealthAlerts`

## 6. 最小回归建议
- 前端：
  - `SettingsView.test.js`: 阈值驱动风险变化 + 健康更新时间可见
  - `ChatView.test.js`: 高风险横幅可见 + 静默开关开启后隐藏
- 后端：
  - `test_health_router.py`: `alert_level/alert_thresholds`
  - `test_runtime_surface_service.py`: 顶层 `failover_thresholds`
  - `test_runtime_surface_config_service.py`: 阈值更新与校验
