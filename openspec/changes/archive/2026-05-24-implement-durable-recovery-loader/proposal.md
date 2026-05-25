# implement-durable-recovery-loader

## Why

The platform has durable workspace posture, checkpoint/resume cursor, registry-backed continuation reattach, and recovery operation evidence. The remaining production gap is a durable recovery loader that can reconstruct a run from persisted workspace state and safely reattach executable continuations when registry bindings allow it.

## What Changes

- Add durable recovery loader contract and service boundary.
- Load persisted run snapshot, events, approval state, continuation descriptors, and recovery operation history.
- Reattach executable continuations only through registered bindings.
- Fail closed when durable state or binding evidence is incomplete.

## Impact

- 收口对象：Embedded workspace store, SDK recovery probe/entrypoints, runtime surface recovery read model, docs/specs/tests.
- 非目标：不 treat in-process maps as durable storage；不 deserialize arbitrary callables；不 bypass checkpoint/resume cursor readiness。
