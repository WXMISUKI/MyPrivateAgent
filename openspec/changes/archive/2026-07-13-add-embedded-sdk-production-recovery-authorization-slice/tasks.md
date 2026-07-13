## 1. Specification Freeze

- [x] 1.1 Add the Embedded SDK production recovery authorization proposal, design, and spec deltas
- [x] 1.2 Sync impacted capabilities and non-goals across persistence interface, runtime surface, and recovery docs
- [x] 1.3 Confirm the change stays fail-closed, opt-in, and non-executable before implementation

## 2. Authorization Contract

- [x] 2.1 Add a side-effect-free Embedded SDK production recovery authorization contract builder in the persistence/recovery layer
- [x] 2.2 Reuse existing production recovery gate, worker ownership enablement input, audit, and loader handoff evidence instead of introducing new execution paths
- [x] 2.3 Add focused backend tests for blocked and ready authorization dry-run outcomes

## 3. Runtime Surface Projection

- [x] 3.1 Surface authorization summaries through the Embedded SDK Runtime Surface builder for `default_runtime_recovery` and `run_recovery`
- [x] 3.2 Keep run-specific recoverability separate from production authorization readiness in the read model
- [x] 3.3 Add focused Runtime Surface tests for the new authorization summary fields

## 4. Gate Coverage

- [x] 4.1 Add runtime contract smoke coverage for Embedded SDK production recovery authorization
- [x] 4.2 Normalize the new smoke evidence into quality gate summary, runtime contract gate, and snapshot coverage
- [x] 4.3 Verify the new contract can fail closed when coverage is missing or incomplete

## 5. Review And Archive Readiness

- [x] 5.1 Update architecture and roadmap truth sources for the new authorization slice
- [x] 5.2 Write a stage review or implementation review that records scope, evidence, and next allowed action
- [x] 5.3 Validate the OpenSpec change and focused tests before archive preparation
