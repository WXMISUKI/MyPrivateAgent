## 1. Specification

- [x] Add runtime worker ownership contract requirements for the PostgreSQL advisory lock execution seam.
- [x] Add production gate requirements for execution seam blocker evidence.

## 2. Implementation

- [x] Add opt-in `PostgresAdvisoryLockExecutionSeam` and execution seam contract builder.
- [x] Embed execution seam evidence into the PostgreSQL vendor lock probe contract.
- [x] Surface execution seam evidence through worker ownership production gate evidence.
- [x] Export the new seam and builder from the agent framework package.

## 3. Quality Gates

- [x] Add focused worker ownership tests for default blocked and injected-executor execution paths.
- [x] Extend runtime smoke with execution seam evidence.
- [x] Extend quality gate and runtime contract gate summaries.
- [x] Update runtime contract and roadmap documentation.

## 4. Verification

- [x] Run focused backend unittest suite.
- [x] Run runtime contract smoke.
- [x] Run quality gate report.
- [x] Validate the OpenSpec change and canonical specs.
- [x] Archive the OpenSpec change after successful verification.
