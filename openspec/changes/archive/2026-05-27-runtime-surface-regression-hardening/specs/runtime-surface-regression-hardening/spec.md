# runtime-surface-regression-hardening Specification

## ADDED Requirements

### Requirement: Runtime Surface SDK reader uses the configured runtime factory
Runtime Surface SHALL build SDK reader contracts through the configured runtime factory seam.

#### Scenario: SDK reader uses default runtime factory
- **GIVEN** Runtime Surface is initialized with a patched default runtime factory
- **WHEN** the SDK reader contract is requested
- **THEN** the factory `create_sdk` path is used
- **AND** the reader observes the SDK contract produced by that factory

### Requirement: Embedded bootstrap validation fails closed for malformed contracts
Runtime Surface SHALL not raise an exception when embedded bootstrap validation receives a non-mapping or mock-like contract.

#### Scenario: Mock-like bootstrap contract is validated
- **GIVEN** a bootstrap update path supplies a contract that is not a concrete mapping
- **WHEN** recovery validation runs
- **THEN** the validation returns a degraded/blocked contract summary
- **AND** the update path can continue applying the requested workspace store mode

### Requirement: Child executor replay preserves explicitly authorized execution record status
Runtime Surface SHALL preserve the execution status stored in child executor replay records when the fixture or caller satisfies child executor execution prerequisites.

#### Scenario: Executed child record remains executed
- **GIVEN** a child executor fixture includes `explicit_executor_binding_opt_in = true`
- **AND** the resulting child executor replay record contains `execution_status = executed`
- **WHEN** Runtime Surface returns child executor replay and summary data
- **THEN** the replay record status remains `executed`
- **AND** side-effect-free preflight or promotion gates do not overwrite it with `blocked`
