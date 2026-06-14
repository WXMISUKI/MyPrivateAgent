## Why

Embedded SDK already supports reviewer and fallback callables in the minimal execution loop, but the SDK contract does not yet explicitly declare the reviewer/fallback event payloads as stable governance evidence. The next valuable hardening step is to make review and fallback outcomes machine-readable and test-covered without expanding to real model execution or default chat behavior.

## What Changes

- Add an explicit Embedded SDK execution-loop reviewer/fallback contract.
- Declare stable event status kinds and required payloads for review, review rejection, fallback applied, and fail-closed loop failure.
- Add focused tests that validate reviewer pass, reviewer rejection, handled fallback, and fail-closed fallback payloads.
- Preserve the existing execution loop behavior; this change tightens contract visibility and validation.

收口对象：Embedded SDK execution loop reviewer/fallback governance evidence.

非目标：

- Do not call a real LLM provider.
- Do not change `/api/chat`.
- Do not add a new framework adapter or provider.
- Do not redesign ExecutionLoopController.
- Do not implement complex multi-agent reviewer routing.

## Capabilities

### New Capabilities

- `embedded-sdk-execution-loop-reviewer-fallback`: defines stable reviewer/fallback event payload contracts for the Embedded SDK execution loop.

### Modified Capabilities

- None.

## Impact

- Backend SDK contract: event status kind declarations and payload validation.
- Tests: focused Embedded SDK / Agent Harness tests for review and fallback event payloads.
- Docs/specs: runtime contracts and roadmap notes.
- APIs: no public endpoint shape change.
