## Design

### Lifecycle Contract

The lifecycle helper classifies each persisted continuation descriptor without executing it:

- `created`: descriptor exists but has no usable binding evidence.
- `bound`: descriptor has at least one binding id but not all required bindings are resolved.
- `ready`: descriptor has binding evidence and all required bindings are resolved.
- `stale`: descriptor is no longer recoverable because the approval/run state has moved past the waiting point.
- `resolved`: descriptor was consumed or deleted after recovery completed.
- `unsafe`: descriptor contains callable-like payloads or runtime-only state.

The first implementation focuses on persisted descriptor classification inside `DurableRecoveryLoader`. `resolved` remains part of the contract vocabulary and can be emitted by future descriptor deletion/operation history work; this slice does not add descriptor tombstone storage.

### Evidence Shape

DurableRecoveryLoader will expose:

- `descriptor_lifecycle.contract_version`
- `descriptor_lifecycle.governed`
- `descriptor_lifecycle.allowed_states`
- `descriptor_lifecycle.descriptor_count`
- `descriptor_lifecycle.states`
- `descriptor_lifecycle.all_ready`
- `descriptor_lifecycle.unsafe_descriptor_keys`
- `descriptor_lifecycle.fail_closed_reason`

The loader also keeps per-descriptor `lifecycle_state` in `continuation_descriptors`.

### Gate Semantics

`build_embedded_sdk_persistence_interface()` may mark `descriptor_lifecycle_governance` ready because the runtime now has a canonical lifecycle classifier. The durable workspace production recovery gate still remains blocked by loader handoff, worker ownership, rollout, audit, and related sections.

### Non-Goals

- No cross-process recovery executor.
- No callable deserialization.
- No production default recovery enablement.
- No descriptor tombstone persistence.
