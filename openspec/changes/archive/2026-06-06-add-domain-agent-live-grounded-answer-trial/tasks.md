## 1. Specification

- [x] 1.1 Create proposal, design, delta specs, and task list for the live grounded-answer trial.

## 2. Implementation

- [x] 2.1 Add `DomainAgentLiveGroundedAnswerTrialService` with explicit provider retrieve and manifest RAG source scope.
- [x] 2.2 Add a CLI script for local explicit live trial execution.
- [x] 2.3 Update docs with live trial command and non-goal boundaries.

## 3. Verification

- [x] 3.1 Add focused unit tests for go, insufficient evidence, missing agent/source, and provider failure cases.
- [x] 3.2 Run focused backend tests for live trial and existing grounded-answer chain.
- [x] 3.3 Run `openspec validate add-domain-agent-live-grounded-answer-trial --strict`.

## 4. Archive

- [x] 4.1 Mark tasks complete after verification.
- [x] 4.2 Archive the change and run `openspec validate --all --strict`.
