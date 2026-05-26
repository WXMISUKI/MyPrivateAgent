## ADDED Requirements
### Requirement: Child Executor Preflight Must Normalize Context Budget Policy
Child executor preflight MUST normalize context budget evidence through a read-only policy contract instead of treating any non-empty budget field as sufficient.

#### Scenario: Preflight has no bounded budget
- **WHEN** child executor preflight is evaluated without a supported positive context budget limit
- **THEN** preflight MUST keep `child_context_budget_defined` in missing requirements
- **AND** it MUST expose `child_executor_context_budget_policy` with blocked status

#### Scenario: Preflight has bounded budget
- **WHEN** child executor preflight receives a supported positive context budget limit
- **THEN** preflight MUST mark `child_context_budget_defined` as satisfied
- **AND** it MUST expose the normalized policy evidence without creating a child run or starting an executor
