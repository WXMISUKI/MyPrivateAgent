## 1. Spec And Contract

- [x] 1.1 Align the change artifacts and delta spec for workflow invoke entrypoint unification.
- [x] 1.2 Update runtime contract documentation to state that workflow invoke API is a capability runtime alias, not a second execution chain.

## 2. Backend Implementation

- [x] 2.1 Route `POST /api/coze-workflows/{workflow_id}/invoke` through capability runtime using the workflow capability id.
- [x] 2.2 Preserve workflow-scoped 404 handling for unknown workflow ids while reusing capability runtime envelopes for business failures.

## 3. Verification

- [x] 3.1 Add focused backend coverage for workflow route and capability route envelope consistency.
- [x] 3.2 Run strict OpenSpec validation and focused backend tests for coze workflow invocation.

## 4. Archive

- [x] 4.1 Archive the change after implementation and validation complete.
