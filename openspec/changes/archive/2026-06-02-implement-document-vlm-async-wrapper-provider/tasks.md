## 1. Spec

- [x] 1.1 Create OpenSpec proposal, design, and requirement delta for Stage 3B wrapper provider.
- [x] 1.2 Define provider endpoints, job lifecycle, and local-development boundaries.

## 2. Implementation

- [x] 2.1 Add a standalone FastAPI async VLM wrapper provider script.
- [x] 2.2 Implement in-memory job lifecycle and background execution.
- [x] 2.3 Delegate parsing to configurable upstream sync provider.
- [x] 2.4 Normalize job status and result payloads for MyPrivateAgent async adapter.

## 3. Documentation

- [x] 3.1 Add startup command and env configuration to VLM async evaluation guide.
- [x] 3.2 Add Stage 3B acceptance command using the existing smoke script.

## 4. Verification

- [x] 4.1 Run focused syntax checks for wrapper and smoke scripts.
- [x] 4.2 Run backend capability provider contract tests.
- [x] 4.3 Run local Stage 3B smoke against MyPrivateAgent and the wrapper provider when services are available.
