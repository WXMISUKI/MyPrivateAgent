## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and tasks for the scheduler fan-out local trial.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a `SchedulerFanoutLocalTrialService` that reuses `SchedulerService` with an in-memory plan/item.
- [x] 2.2 Support success, partial-failure, and blocked local trial modes.
- [x] 2.3 Add a CLI script with mode, child roles, objective, item title, and pretty JSON options.
- [x] 2.4 Update runtime roadmap/docs with the local scheduler trial command and boundaries.

## 3. Verification And Archive

- [x] 3.1 Add focused tests for go, review, blocked, boundary preservation, child id fields, and CLI exit codes.
- [x] 3.2 Run focused scheduler fan-out local trial tests.
- [x] 3.3 Run `openspec validate add-scheduler-fanout-local-trial --strict`.
- [x] 3.4 Run the local scheduler fan-out CLI in success and partial-failure modes.
- [x] 3.5 Run `openspec validate --all --strict`.
- [x] 3.6 Sync canonical spec and archive the OpenSpec change.
