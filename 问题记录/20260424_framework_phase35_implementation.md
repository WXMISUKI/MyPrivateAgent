# Phase 35 实施记录：历史重复反馈清理脚本

## 本次目标
- 提供可重复执行的数据治理脚本，清理 `message_feedback` 历史重复记录。
- 支持预览模式，先评估影响再执行删除，降低生产风险。

## 主要改动

### 1. 新增反馈维护服务
- 文件：`backend/services/feedback_maintenance_service.py`
- 能力：
  - 构建重复分组去重计划（按 `conversation_id + message_id + user_id`）
  - 保留最新记录，删除重复记录
  - 若保留记录缺失 `created_learning_id`，可从重复记录继承
  - 支持 `dry_run`、`include_null_message`、`limit_groups`

### 2. 新增 CLI 清理脚本
- 文件：`backend/scripts/dedupe_message_feedback.py`
- 默认行为：
  - dry-run 预览（不删数据）
- 可选参数：
  - `--apply` 真正执行删除
  - `--include-null-message` 包含 `message_id IS NULL` 分组
  - `--limit-groups N` 分批处理
  - `--json` 输出机器可读结果

### 3. 测试补充
- 文件：`tests/agent_framework/test_feedback_maintenance_service.py`
- 覆盖点：
  - 去重保留最新记录
  - 继承 `created_learning_id`
  - apply 模式真实删除与提交

## 验证结果
- 单测通过：
  - `python -m unittest tests.agent_framework.test_feedback_maintenance_service tests.agent_framework.test_conversation_service tests.agent_framework.test_chat_service tests.agent_framework.test_orchestrator_service`
- 脚本预览验证：
  - `python backend/scripts/dedupe_message_feedback.py --preview-limit 10`
  - 当前环境结果：`groups_total=0`（暂无历史重复）

## 建议操作流程
1. 先跑 dry-run：确认重复规模。
2. 如有重复，先执行小批次 `--apply --limit-groups 50`。
3. 观察 analytics 指标稳定后再全量执行。
