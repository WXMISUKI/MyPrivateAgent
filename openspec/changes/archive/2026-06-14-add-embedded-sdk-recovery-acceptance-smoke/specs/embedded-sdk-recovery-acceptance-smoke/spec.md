## ADDED Requirements

### Requirement: Acceptance smoke MUST emit compact recovery readiness evidence

The system MUST provide a deterministic Embedded SDK recovery acceptance smoke that emits a compact JSON evidence payload for explicit embedded runtime consumers.

#### Scenario: Accepted durable registry-backed recovery path

- **WHEN** the smoke runs with durable workspace evidence and required continuation registry bindings
- **THEN** the payload MUST report `contract_version = embedded-sdk-recovery-acceptance-smoke-v1`
- **AND** it MUST report `decision = accepted`
- **AND** it MUST include workspace backend evidence, recovery entrypoints, tool continuation evidence, loop continuation evidence, and latest recovery operation evidence
- **AND** it MUST state that accepted does not enable worker lease, background auto recovery, default chat grounding, or real LLM execution

#### Scenario: Memory-only workspace is blocked

- **WHEN** the smoke runs against a memory-only workspace posture
- **THEN** the payload MUST report `decision = blocked`
- **AND** blockers MUST include a machine-readable durable workspace blocker
- **AND** the payload MUST NOT claim cross-process durable recovery readiness

#### Scenario: Missing registry binding is blocked

- **WHEN** persisted continuation descriptors exist but the current registry cannot resolve a required binding
- **THEN** the payload MUST report `decision = blocked`
- **AND** blockers MUST include a machine-readable registry binding blocker
- **AND** recovery entrypoints MUST remain explicit and non-executed beyond the controlled failed-closed scenario

### Requirement: Acceptance evidence MUST be non-executable and safe to archive

The acceptance smoke MUST sanitize its evidence so it can be stored in docs, CI artifacts, or issue records without copying executable runtime objects.

#### Scenario: Unsafe runtime objects are excluded

- **WHEN** the acceptance payload is generated
- **THEN** it MUST NOT include Python callable objects, executable handlers, provider clients, active stream iterators, or raw SDK object instances
- **AND** it MAY include stable binding ids, handler names, recovery reasons, compact metadata, and state summaries

### Requirement: Smoke script MUST expose deterministic process semantics

The acceptance smoke script MUST print JSON only and use deterministic exit codes for automation.

#### Scenario: Script exits zero for accepted evidence

- **WHEN** the script generates an accepted evidence payload
- **THEN** it MUST write JSON to stdout
- **AND** it MUST exit with code `0`

#### Scenario: Script exits blocked for blocked evidence

- **WHEN** the script generates a blocked evidence payload
- **THEN** it MUST write JSON to stdout
- **AND** it MUST exit with code `2`
