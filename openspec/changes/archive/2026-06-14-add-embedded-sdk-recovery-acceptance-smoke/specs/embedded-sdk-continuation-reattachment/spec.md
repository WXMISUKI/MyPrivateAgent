## ADDED Requirements

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
