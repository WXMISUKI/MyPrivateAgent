## ADDED Requirements

### Requirement: Implementation Resume Decision MUST Be Recorded

系统 SHALL 在恢复任何 channel 级实现前记录 implementation resume decision，避免 channel promotion 只存在于对话或局部 momentum 中。

#### Scenario: Resume decision allows implementation

- **WHEN** 团队决定恢复某个 channel 的实现
- **THEN** promotion record SHALL include channel, current layer, target layer, readiness evidence, blockers, decision, next allowed action, and explicit non-goals
- **AND** decision SHALL identify the shallowest eligible target layer
- **AND** implementation SHALL NOT include deeper query layers than the recorded target layer

#### Scenario: Resume decision blocks implementation

- **WHEN** readiness evidence is incomplete or blockers remain
- **THEN** promotion record SHALL set decision to blocked or spec_only
- **AND** next allowed action SHALL be a spec, architecture, or readiness-check slice rather than a new channel feature implementation
