## 1. Runtime Surface Contract

- [x] 1.1 Add focused tests for `external_adapter_recent_summary` recorded and unavailable states.
- [x] 1.2 Add an external adapter recent summary builder using Query Control trace events only.
- [x] 1.3 Expose `external_adapter_recent_summary` through Runtime Surface and Runtime Profile.
- [x] 1.4 Add a dedicated `/api/runtime-profile/external-adapter-recent-summary` endpoint.
- [x] 1.5 Feed Channel Promotion Gate with real external adapter recent summary readiness while keeping deeper layers blocked.

## 2. Contract Guards And Docs

- [x] 2.1 Update Runtime Contract Snapshot stable fields if the Runtime Profile surface changes.
- [x] 2.2 Sync canonical OpenSpec specs with the new recent summary boundary.
- [x] 2.3 Update architecture, recent summary abstraction note, and roadmap.

## 3. Verification And Archive

- [x] 3.1 Run focused backend unittest verification.
- [x] 3.2 Validate the OpenSpec change strictly.
- [x] 3.3 Validate canonical OpenSpec specs strictly.
- [x] 3.4 Archive the completed OpenSpec change.
