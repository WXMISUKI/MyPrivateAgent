## MODIFIED Requirements

### Requirement: Phase I Exit Gate

当团队进入 `Phase I` 后，系统 SHALL 明确什么时候允许恢复新的 channel 实现，什么时候应继续停留在规格/架构层。

#### Scenario: Resume Implementation

- **WHEN** 同时满足以下条件：
  - 高层真源稳定
  - channel promotion gate 有正式记录
  - recent summary 抽象判断已有明确当前结论
  - 下一步实现目标从该 channel 当前允许的最浅层开始
  - 本次实现明确列出不会越级推进的非目标
- **THEN** 团队 MAY 恢复新的 channel 级实现
- **AND** 恢复时应优先从最浅层、最小试点开始
- **AND** 不得在同一 change 中顺手推广到更深层 query 能力

#### Scenario: Stay in Spec Layer

- **WHEN** 存在以下任一情况：
  - 新增 channel 的推广顺序还在摇摆
  - canonical spec 之间仍有冲突
  - 团队对 channel-specific / generic 的边界还没统一
  - channel promotion gate 尚未记录当前层级与下一允许动作
  - 下一步实现会同时触碰 detail/history/workspace 多层能力
- **THEN** 团队 SHALL 继续停留在规格/架构层
- **AND** 不得默认恢复新的 channel 实现
