# MyPrivateAgent 问题记录索引（精简版）

## 1. 当前总览（优先阅读）
- [20260424_framework_current_status_summary.md](./20260424_framework_current_status_summary.md)：框架现状、缺口、下一步优先级

## 2. 框架实施阶段记录（Phase）
当前阶段文档采用统一命名：
- `20260422_framework_phase{N}_implementation.md`
- `20260423_framework_phase{N}_implementation.md`
- `20260424_framework_phase{N}_implementation.md`

建议按顺序阅读：
1. 基础抽离与执行链收口：Phase 1 ~ Phase 17  
2. preset / auth / runtime 治理增强：Phase 18 ~ Phase 27  
3. 反馈闭环与治理能力：Phase 28 ~ Phase 35
4. Planner 调度器第一版：Phase 36 ~ Phase 42
5. Skill Runtime 第一版：Phase 43 ~ Phase 44
6. 运行稳定性收口：Phase 45 ~ Phase 49
7. Demo 默认本地存储：Phase 50
8. Demo 手册收口：Phase 51
9. 停止生成 smoke / 测试手册 / 文档索引收口：Phase 52

关键里程碑：
- [20260424_framework_phase30_implementation.md](./20260424_framework_phase30_implementation.md)：starter/demo 产品化
- [20260424_framework_phase31_implementation.md](./20260424_framework_phase31_implementation.md)：反馈关联 runtime effect
- [20260424_framework_phase33_implementation.md](./20260424_framework_phase33_implementation.md)：消息级 feedback 精确绑定 + analytics 工作台
- [20260424_framework_phase34_implementation.md](./20260424_framework_phase34_implementation.md)：反馈幂等约束
- [20260424_framework_phase35_implementation.md](./20260424_framework_phase35_implementation.md)：历史重复反馈清理脚本
- [20260425_framework_phase36_implementation.md](./20260425_framework_phase36_implementation.md)：真实多智能体调度器第一版
- [20260425_framework_phase37_implementation.md](./20260425_framework_phase37_implementation.md)：并发 Fan-Out 调度第一版
- [20260425_framework_phase38_implementation.md](./20260425_framework_phase38_implementation.md)：Scheduler Timeout / Retry / Cancellation 第一版
- [20260425_framework_phase39_implementation.md](./20260425_framework_phase39_implementation.md)：Scheduler Audit Trail 与 Planner Timeline 第一版
- [20260425_framework_phase40_implementation.md](./20260425_framework_phase40_implementation.md)：Unified Run Trace 第一版
- [20260425_framework_phase41_implementation.md](./20260425_framework_phase41_implementation.md)：Runtime Tool / MCP / Permission Run Trace 第一版
- [20260425_framework_phase42_implementation.md](./20260425_framework_phase42_implementation.md)：Permission Approval Run Trace 与 Router 级 Trace Service
- [20260425_framework_phase43_implementation.md](./20260425_framework_phase43_implementation.md)：Skill Runtime Selection / Injection 第一版
- [20260425_framework_phase44_implementation.md](./20260425_framework_phase44_implementation.md)：Skill Priority / Activation / Conflict Policy 第一版
- [20260425_framework_phase45_implementation.md](./20260425_framework_phase45_implementation.md)：启动自检 / 健康检查 / 最小 Smoke 第一版
- [20260425_framework_phase46_implementation.md](./20260425_framework_phase46_implementation.md)：Auth / Conversation Smoke 第一版
- [20260426_framework_phase47_implementation.md](./20260426_framework_phase47_implementation.md)：Chat SSE Smoke 与 Fallback Done 收口
- [20260426_framework_phase48_implementation.md](./20260426_framework_phase48_implementation.md)：Chat Empty Response / Error 收口
- [20260426_framework_phase49_implementation.md](./20260426_framework_phase49_implementation.md)：前端回归闭环与 Chat Error Event Smoke
- [20260426_framework_phase50_implementation.md](./20260426_framework_phase50_implementation.md)：Demo 默认 SQLite，本地优先存储模式
- [20260426_framework_phase51_implementation.md](./20260426_framework_phase51_implementation.md)：Demo 运行与演示手册收口
- [20260426_framework_phase52_implementation.md](./20260426_framework_phase52_implementation.md)：停止生成链路收口、测试手册、文档索引整理

## 3. 设计文档
- [20260413_enterprise_agent_architecture_design.md](./20260413_enterprise_agent_architecture_design.md)
- [20260413_multi_agent_v2_design.md](./20260413_multi_agent_v2_design.md)
- [20260413_self_improvement_design.md](./20260413_self_improvement_design.md)
- [20260417_framework_improvement_plan.md](./20260417_framework_improvement_plan.md)
- [20260422_harness_maturity_upgrade_plan.md](./20260422_harness_maturity_upgrade_plan.md)

## 4. 问题修复与测试记录
- [20260309_sse_stream_fix.md](./20260309_sse_stream_fix.md)
- [20260422_doubao_tool_call_weather_fix.md](./20260422_doubao_tool_call_weather_fix.md)
- [20260414_test_cases.md](./20260414_test_cases.md)

## 5. 历史归档说明
- 已删除废弃/冗余文件：`20260413_multi_agent_design.md`（被 v2 取代）、运行日志与临时文本（`console.txt`、`error.txt`、`对话记录.txt`、`豆包工具调用简易实力.txt`）。
- 如需回溯旧策略，请优先查阅 `Phase` 文档与当日 summary，而不是临时日志。

---
最后更新时间：2026-04-25
