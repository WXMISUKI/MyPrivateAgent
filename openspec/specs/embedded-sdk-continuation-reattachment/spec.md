# embedded-sdk-continuation-reattachment Specification

## Purpose
Define how the Embedded SDK may reattach executable continuations from safe registry bindings while preserving fail-closed recovery boundaries.
## Requirements
### Requirement: Embedded SDK Must Expose A Continuation Registry Seam

`EmbeddedAgentRuntimeSDK` MUST support an injectable continuation registry/resolver seam so persisted continuation descriptors can be reattached to executable continuations in a new process when an explicit binding exists.

#### Scenario: Tool continuation becomes recoverable via registry

- **GIVEN** a run pauses on tool approval
- **AND** the persisted tool continuation descriptor contains a stable tool executor binding id
- **AND** a new SDK instance is created with a continuation registry that can resolve that binding id
- **WHEN** `probe_run_recovery(run_id)` is called
- **THEN** the tool continuation MUST be reported as recoverable
- **AND** the recovery reason MUST distinguish registry-based availability from in-process availability

### Requirement: Recovery Attempt Must Reattach Continuations Through The Same Resolver Path

The SDK MUST use the same registry-aware resolver logic for both `probe_run_recovery()` and actual recovery attempts.

#### Scenario: Approved tool continuation resumes in a new process

- **GIVEN** a run has a persisted tool continuation descriptor with a stable binding id
- **AND** a new SDK instance can resolve that binding id through the continuation registry
- **WHEN** `submit_approval(request_id, "approved")` is called
- **THEN** the SDK MUST reattach the executable tool continuation
- **AND** the tool executor MUST run successfully
- **AND** the SDK MUST NOT fail with `missing_executable_continuation`

#### Scenario: Loop continuation resumes in a new process

- **GIVEN** a run has a persisted loop continuation descriptor with stable binding ids for its optional loop callables
- **AND** a new SDK instance can resolve those binding ids
- **WHEN** `resume_run(run_id, continue_loop=True)` is called
- **THEN** the SDK MUST reattach the loop continuation
- **AND** the run MUST continue through the remaining loop states

### Requirement: Missing Registry Bindings Must Still Fail Closed

The SDK MUST keep fail-closed behavior when a persisted binding id cannot be resolved.

#### Scenario: Persisted binding id is missing from the registry

- **GIVEN** a persisted continuation descriptor contains one or more binding ids
- **AND** the current SDK instance cannot resolve at least one required binding id
- **WHEN** `probe_run_recovery(run_id)` or the corresponding recovery attempt runs
- **THEN** the SDK MUST report the continuation as unrecoverable
- **AND** the recovery reason MUST be `missing_registered_binding`
- **AND** recovery MUST remain blocked

### Requirement: Continuation reattachment MUST be covered by acceptance smoke

Registry-backed continuation reattachment MUST be covered by the Embedded SDK recovery acceptance smoke for both tool approval continuation and loop continuation.

#### Scenario: Tool and loop continuations are accepted through registry bindings

- **WHEN** a durable run persists tool and loop continuation descriptors with stable binding ids
- **AND** a new SDK or facade instance resolves those ids from the continuation registry
- **THEN** the acceptance smoke MUST report tool continuation recovery as registry-backed
- **AND** it MUST report loop continuation completion through `resume_run(..., continue_loop=True)`

#### Scenario: Unresolved binding blocks acceptance

- **WHEN** a required persisted continuation binding id cannot be resolved
- **THEN** the acceptance smoke MUST report `decision = blocked`
- **AND** the blocker MUST identify missing registry binding evidence
