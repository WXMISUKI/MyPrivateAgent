## 1. Specification

- [x] 1.1 Create proposal, design, and spec for the local document RAG operator entrypoint.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Backend Implementation

- [x] 2.1 Add a local operator entrypoint service that composes readiness and upload-to-use loop.
- [x] 2.2 Add backend API endpoints for readiness and local trial.
- [x] 2.3 Register the router in the server router registry.

## 3. Frontend Implementation

- [x] 3.1 Add frontend API methods for local document RAG readiness and trial.
- [x] 3.2 Add a compact Settings diagnostics operator card.
- [x] 3.3 Display decision, reason, source id, report paths, and raw JSON details.

## 4. Verification

- [x] 4.1 Add focused backend tests for readiness, blocked readiness short-circuit, and trial pass-through.
- [x] 4.2 Add focused frontend tests for readiness and trial actions.
- [x] 4.3 Run focused backend and frontend tests.
- [x] 4.4 Run `openspec validate --all --strict`.

## 5. Archive

- [x] 5.1 Run or refresh a local operator readiness report where local dependencies are available.
- [x] 5.2 Update architecture/docs notes with the new operator entrypoint.
- [x] 5.3 Archive the OpenSpec change after implementation and validation.
