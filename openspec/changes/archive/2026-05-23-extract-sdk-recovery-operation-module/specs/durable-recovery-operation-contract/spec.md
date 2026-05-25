# durable-recovery-operation-contract Specification Delta

## MODIFIED Requirements

### Requirement: Recovery operation records MUST be compact and non-executable

Recovery operation records MUST contain audit evidence without copying executable internals, and their contract construction SHOULD live behind a dedicated recovery operation Module rather than inside the SDK orchestration class.

#### Scenario: Operation record is emitted

- **WHEN** the SDK records a recovery operation
- **THEN** the record MUST include operation id, run id, entrypoint, operation status, reason fields, checkpoint/cursor references, continuation reference, workspace evidence, and persistence posture
- **AND** it MUST NOT include Python callable objects, executable handlers, provider clients, or active stream iterators
- **AND** the SDK orchestration path SHOULD delegate recovery operation record construction to the dedicated recovery operation Module
