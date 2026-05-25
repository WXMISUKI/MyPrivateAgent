## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose production default enablement input source evidence

The worker ownership runtime contract MUST expose a read-only input source contract for production default ownership enablement requests.

#### Scenario: Enablement input source defaults to blocked

- **WHEN** the production default enablement input source contract is built without source metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source, request, approval, target store mode, rollout artifact, vendor lock decision, renewal lifecycle, auto-claim decision, audit, rollback, and fallback evidence
- **AND** it MUST NOT enable production default worker ownership

#### Scenario: Enablement strategy embeds input source evidence

- **WHEN** the production enablement strategy is built
- **THEN** it MUST include the nested input source contract
- **AND** blocked input source evidence MUST keep production default allowment false even when an explicit enablement boolean is requested

#### Scenario: Complete input source remains descriptive

- **WHEN** a production default enablement input source includes a valid source kind, request id, requester, approval time, strict SQL target mode, rollout artifact, vendor lock decision, renewal lifecycle reference, auto-claim decision, audit evidence, rollback plan, and fallback policy
- **THEN** the input source MAY report `overall_status = ready`
- **AND** it MUST remain descriptive evidence until all production gate sections are ready and explicit default enablement is requested
