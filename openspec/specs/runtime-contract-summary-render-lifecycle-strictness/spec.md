# runtime-contract-summary-render-lifecycle-strictness Specification

## Purpose
Define strict rendering behavior for runtime contract summary fields in quality gate Markdown output.
## Requirements
### Requirement: Markdown summary MUST render lifecycle recovery coverage fail-closed

The Quality Gate Markdown summary MUST render approval lifecycle recovery coverage using the same evidence predicate as Runtime Contract Gate.

#### Scenario: Summary flag is true but evidence disagrees

- **WHEN** a report has `approval_lifecycle_recovery_coverage.alignment_smoke = true`
- **AND** at least one evidence field disagrees with `replayed / ignored / already_resolved`
- **THEN** the Runtime Contract Summary table MUST render approval lifecycle recovery coverage as `no`.

#### Scenario: Summary evidence is complete

- **WHEN** a report has complete approval lifecycle recovery evidence
- **THEN** the Runtime Contract Summary table MAY render approval lifecycle recovery coverage as `yes`.
