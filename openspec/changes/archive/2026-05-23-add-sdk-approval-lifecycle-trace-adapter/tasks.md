## 1. Specs and Contract Shape

- [x] 1.1 Validate the new OpenSpec change in strict mode.
- [x] 1.2 Add focused tests for opt-in approval lifecycle trace recording.
- [x] 1.3 Add focused tests for fail-open recorder behavior.
- [x] 1.4 Add focused tests for dedupe-key behavior on replay/ignored lifecycle events.

## 2. Adapter Implementation

- [x] 2.1 Implement a small SDK approval lifecycle trace adapter/service that maps selected SDK events to runtime trace payloads.
- [x] 2.2 Wire the adapter into `EmbeddedAgentRuntimeSDK` through an explicit optional dependency.
- [x] 2.3 Ensure recorded payloads stay compact and exclude executable continuation internals.
- [x] 2.4 Ensure recorder failures do not alter approval decisions, recovery reasons, or SDK event stream output.

## 3. Docs and Verification

- [x] 3.1 Update `docs/architecture/runtime_contracts.md` with the SDK approval lifecycle trace adapter boundary.
- [x] 3.2 Update `docs/roadmap/next_phase_hardening.md` with current progress and remaining boundaries.
- [x] 3.3 Update `docs/test_manual.md` with focused verification notes.
- [x] 3.4 Run `cmd /c openspec validate add-sdk-approval-lifecycle-trace-adapter --strict`.
- [x] 3.5 Run focused backend tests for the new adapter and Embedded SDK approval lifecycle.
