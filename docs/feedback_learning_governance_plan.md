# 反馈与学习治理规划

## 目标

把当前已经打通的 `feedback -> runtime_knowledge_effect -> learning` 最小闭环，继续收口成可治理、可回看、可分析、可回滚的学习系统。

## 当前已完成

- 后端已支持消息级反馈提交。
- 反馈会关联最近的 `runtime_knowledge_effect`。
- 负反馈会自动生成 `Learning` 记录。
- `Learning` 已具备 `source / pattern_key / tags / see_also / created_learning_id` 等治理字段。
- 前端消息卡已回显：
  - `scope`
  - `selected_count`
  - `prompt_keys`
  - `practice_ids`
  - `created_learning_id`
- `FeedbackAnalyticsView` 已支持：
  - `scope`
  - `prompt`
  - `practice`
  - 回滚候选
- `LearningsView` 已作为学习记录总览页存在。
- 已完成 P0 可钻取闭环：
  - `FeedbackAnalyticsView` 可跳到对应学习记录
  - `ChatMessageItem` 可直达关联 `learning`
  - `LearningsView` 支持按 `source / pattern_key / tag / learning_id` 钻取筛选
  - `Learning.details / tags` 已写入 `prompt_key / practice_id` 证据
- 已完成第一批学习治理动作：
  - `disable`
  - `rollback`
  - `restore`
  - `promote`
  - `LearningsView` 已具备治理按钮和状态呈现
- `promote` 已升级为真实知识转化：
  - `best_practice` 会产出 `BestPractice`
  - `system_prompt` 会产出 `SystemPrompt`
  - 学习状态会同步推进到对应提升状态
- 已补学习审核闭环：
  - `LearningReviewRecord` 记录审核历史
  - `LearningsView` 支持提交审核
  - 列表页展示最新审核状态与质量分
  - 统计卡展示已审核数量与平均质量
- 已补学习版本历史与冲突提示：
  - `LearningVersionRecord` 记录学习版本快照
  - `LearningsView` 支持展开版本历史
  - 列表页展示历史版本数与冲突标签
  - 学习详情/列表会返回 `history_count` 与 `conflict_flags`
- 已支持版本对比
- 已支持重复模式项合并
- 已支持从历史版本回写当前学习
- 已支持字段级选择性回写
- 已支持学习治理 `snapshot_ref` 回显
- 已接入统一治理时间线：
  - `GovernanceTimelinePanel` 已可展示 `learning_version_applied`
  - Learning 已成为独立治理域
  - Learning 快照可参与统一视图复制与 `snapshot` 命令跳转
  - `disable / rollback / restore / promote / review / merge-duplicate / apply-version`
    已支持统一 `snapshot_ref + timeline_recording`
  - `LearningsView` 已会附带当前 `conversation_id`，让治理动作可写入当前会话时间线

## 仍然存在的缺口

1. 学习治理还不够完整
- 还缺学习版本的分支对比与变更摘要
- 还缺冲突条目之间的合并/抑制策略
- 还缺审核历史的版本化视图

2. 反馈分析还不够可操作
- 回滚候选还可以进一步扩展到学习来源对照
- 还缺学习效果的趋势比较和回滚前后对照

3. 端到端验证还不够
- 还缺 `message -> feedback -> learning -> analytics` 的完整回归链

## 下一步建议顺序

### P0: 学习记录可钻取

- `LearningsView` 已增加按以下字段过滤：
  - `source`
  - `pattern_key`
  - `tag`
  - `learning_id`
- `FeedbackAnalyticsView` 已支持跳转到对应学习记录
- `ChatMessageItem` 已支持跳转到关联 learning

### P1: 学习治理

- 已完成第一批治理动作：
  - disable
  - rollback
  - restore
  - promote
- 已完成版本历史与冲突提示：
  - `history_count`
  - `conflict_flags`
  - 版本历史展开
- 已完成第一版版本治理动作：
  - 历史版本对比
  - 重复 pattern learning 合并
  - 历史版本回写当前学习
  - 历史版本按字段选择性回写
  - 学习版本治理快照引用
- 下一步补：
  - 学习版本分支对比摘要
  - 冲突条目合并后的人工复核与回滚
  - 学习提升结果的人工复核回写
  - 审核结果的版本化和回溯视图
  - Learning 治理动作继续补齐到统一后端治理时间线分类与前端摘要卡策略

### P2: 反馈分析操作化

- 回滚候选支持点击跳转
- 回滚候选支持按 `prompt_key / practice_id / scope` 筛选
- 增加学习来源与效果的对照视图

### P3: 端到端测试

- 覆盖：
  - assistant message
  - message feedback
  - learning creation
  - analytics aggregation
  - learning list drill-down

## 结论

当前反馈链路已经不再是“只记录反馈”，而是开始具备“反馈驱动学习”的基础。下一阶段最有价值的是把学习记录和反馈分析做成真正可钻取、可回滚、可审计的治理面。
