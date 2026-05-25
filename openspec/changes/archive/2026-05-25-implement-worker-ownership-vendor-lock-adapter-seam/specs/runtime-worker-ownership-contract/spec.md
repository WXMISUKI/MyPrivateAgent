## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose vendor lock adapter seam evidence
The runtime worker ownership contract MUST expose a side-effect-free vendor lock adapter seam contract before vendor-specific lock semantics can be considered production-ready.

#### Scenario: Vendor lock adapter seam defaults to blocked
- **WHEN** the vendor lock adapter seam contract is built without adapter metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing sections for adapter kind, target backend, lock scope, fencing strategy, TTL/renewal strategy, failover strategy, stale owner cleanup, acquire support, renew support, release support, probe support, and production allowment
- **AND** it MUST report SQL row lease/fencing as non-vendor-lock authority

#### Scenario: Vendor lock semantics embeds adapter seam
- **WHEN** `worker_ownership.vendor_lock_semantics` is inspected
- **THEN** its policy MUST include `adapter_contract`
- **AND** a blocked adapter contract MUST keep vendor lock semantics blocked
- **AND** the runtime MUST NOT acquire, renew, release, or probe a vendor lock as a side effect

#### Scenario: Ready adapter seam remains descriptive
- **WHEN** a vendor lock adapter seam includes adapter kind, target backend, scope, fencing, TTL/renewal, failover, stale cleanup, acquire/renew/release/probe support, and production allowment
- **THEN** the adapter seam MAY report `overall_status = ready`
- **AND** it MUST still not enable production default worker ownership by itself
