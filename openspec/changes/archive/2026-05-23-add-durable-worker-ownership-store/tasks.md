## 1. Specification

- [x] 1.1 Define durable worker ownership store scope, non-goals, and affected contract.
- [x] 1.2 Add runtime worker ownership delta spec for SQL-backed durable adapter behavior.

## 2. Implementation

- [x] 2.1 Add SQLAlchemy ownership lease persistence model and migration.
- [x] 2.2 Implement SQLAlchemy runtime worker ownership store with claim, heartbeat, validation, and lease read operations.
- [x] 2.3 Expose SQL adapter contract evidence without changing the default in-memory runtime dependency.

## 3. Verification and Docs

- [x] 3.1 Add focused durable ownership tests for persistence, competing claims, expiration replacement, heartbeat, and stale fencing.
- [x] 3.2 Update runtime architecture and roadmap docs.
- [x] 3.3 Run focused worker ownership tests.
- [x] 3.4 Run OpenSpec strict validation.
- [x] 3.5 Sync canonical specs and archive the completed change.
