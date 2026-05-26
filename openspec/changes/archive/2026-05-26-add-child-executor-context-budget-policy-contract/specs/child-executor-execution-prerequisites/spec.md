## ADDED Requirements
### Requirement: Context Budget Policy Must Be Machine-Readable
Child executor execution prerequisites MUST expose a machine-readable context budget policy for the `child_context_budget_defined` requirement.

The policy evidence MUST include contract version, overall status, readiness boolean, budget source, normalized bounded limits, missing sections, fail-closed reason, next allowed action, and non-goals.

#### Scenario: Context budget policy is missing
- **WHEN** no child executor context budget source is available
- **THEN** `child_executor_execution_prerequisites` MUST keep `child_context_budget_defined` in `missing_requirements`
- **AND** the requirement evidence MUST expose `overall_status = blocked`
- **AND** the evidence MUST list missing budget source or bounded limit sections
- **AND** real executor dispatch MUST remain disabled

#### Scenario: Context budget policy is bounded
- **WHEN** child executor preflight includes a context budget with at least one positive bounded limit
- **THEN** the `child_context_budget_defined` requirement MUST report ready
- **AND** the policy evidence MUST expose the normalized limit and source path
- **AND** this readiness MUST NOT by itself authorize worker dispatch

#### Scenario: Context budget policy is malformed
- **WHEN** a child executor context budget object exists but does not define any supported positive bounded limit
- **THEN** the context budget policy MUST fail closed
- **AND** execution prerequisites MUST remain blocked

### Requirement: Context Budget Policy Must Be Quality-Gated
Runtime smoke, Quality Gate, and Runtime Contract Gate MUST expose coverage evidence for child executor context budget policy readiness.

#### Scenario: Context budget policy smoke is healthy
- **WHEN** runtime contract smoke evaluates child executor prerequisites
- **THEN** it MUST emit default fail-closed context budget policy evidence
- **AND** it MUST emit opt-in bounded budget policy evidence
- **AND** malformed or missing evidence MUST fail closed in the quality gate summary
