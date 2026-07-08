# Runtime Plane Stage Review Protocol

> 每完成一个运行层相关 stage，都必须按这份模板写回顾。目的是防止在推进中逐步偏离最初的边界和非目标。

## When To Use

- 完成 Stage 0 冻结与定位收口后
- 完成任意 Stage 1 竖切后
- 完成治理接入、模板硬化或 adapter promotion gate 后
- 发现工作开始膨胀、边界开始模糊、或想顺手补平台能力时

## Review Template

```text
Stage:
Date:
Owner:
Completed work:
What stayed within scope:
What drifted or got tempting:
What evidence shows the stage is done:
What must not be expanded next:
Is the next stage still justified:
Next allowed action:
Rollback or pause condition:
```

## Review Rules

- 只写事实，不写愿望
- 必须点名当前 stage 的非目标
- 如果发现偏离，优先回 freeze-and-align stage
- 如果下一阶段不再成立，就暂停，不要为了推进而推进
- 回顾要能让后来的人一眼看出“我们有没有按计划执行”

## Stage 0 Example

```text
Stage: Stage 0 - Freeze and alignment
Date: 2026-07-08
Owner: MyPrivateAgent maintainers
Completed work: Control-plane positioning, runtime-plane strategy, OpenSpec change, docs entrypoint updates
What stayed within scope: Documentation and contract boundaries only
What drifted or got tempting: Extending AgentHarnessFacade into production runtime
What evidence shows the stage is done: Strategy doc, spec, tasks, entrypoint links, roadmap note
What must not be expanded next: Do not add platform-like execution features into control-plane code
Is the next stage still justified: Yes, but only as a minimal adapter-backed runtime slice
Next allowed action: Select one minimal runtime-plane slice and implement through adapter boundary
Rollback or pause condition: Runtime work starts to grow into a platform clone
```
