## ADDED Requirements

### Requirement: Recovery protocol MUST be acceptance-smoke verifiable

The Embedded SDK recovery protocol MUST expose enough compact evidence for a deterministic acceptance smoke to verify explicit durable registry-backed recovery consumption without enabling default automatic recovery.

#### Scenario: Acceptance smoke consumes recovery protocol evidence

- **WHEN** the acceptance smoke probes and exercises `submit_approval.approved` and `resume_run.continue_loop`
- **THEN** the recovery protocol MUST provide machine-readable recoverability, entrypoint, recovery reason, and latest operation evidence
- **AND** accepted evidence MUST NOT authorize worker lease, background recovery, distributed execution, or default `/api/chat` behavior changes
