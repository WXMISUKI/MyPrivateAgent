## Why

Several canonical OpenSpec files still contain archive-generated `TBD` Purpose placeholders. That is harmless at runtime, but weakens the specs as enterprise reference material because maintainers cannot quickly see each contract's boundary.

## What Changes

- Add a small meta-spec requiring canonical runtime specs to keep explicit, non-placeholder Purpose sections.
- Replace archive-generated Purpose placeholders in runtime, query/read-model, governance, tool-runtime, and child-executor canonical specs.
- Keep all requirement text and runtime behavior unchanged.

## Capabilities

### New Capabilities

- `canonical-spec-purpose-hygiene`: Ensures canonical specs document their purpose explicitly and do not retain archive scaffold placeholders.

### Modified Capabilities

- None.

## Impact

- 收口对象：OpenSpec canonical spec Purpose hygiene.
- 受影响文件：`openspec/specs/**/spec.md` 中仍保留 archive-generated Purpose 的 runtime/read-model/governance contract specs.
- 受影响代码/API：无。
- 文档真源：OpenSpec canonical specs.
- 非目标：不修改任何 requirement 语义、不改代码、不改测试断言、不扩大 runtime contract shape。
