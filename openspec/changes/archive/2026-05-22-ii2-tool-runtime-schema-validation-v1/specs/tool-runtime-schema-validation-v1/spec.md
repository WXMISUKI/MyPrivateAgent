## ADDED Requirements

### Requirement: Primitive Type Validation

The system MUST fail closed when a supported primitive argument type does not
match the registered tool schema.

#### Scenario: String argument receives integer

- **GIVEN** a tool declares an argument with `type = string`
- **WHEN** the caller passes an integer
- **THEN** `ToolRuntimeService.execute_tool(...)` MUST return
  `status = validation_failed`
- **AND** the tool implementation MUST NOT be invoked.

### Requirement: Enum Validation

The system MUST fail closed when an argument value is outside a supported enum.

#### Scenario: Enum value is unsupported

- **GIVEN** a tool declares an argument with `enum = ["quick", "deep"]`
- **WHEN** the caller passes `other`
- **THEN** the schema validation metadata MUST include `invalid_enum`.

### Requirement: Nested Object Required Validation

The system MUST validate required fields for supported nested object schemas.

#### Scenario: Nested required field is missing

- **GIVEN** a tool declares an object argument with nested `required = ["level"]`
- **WHEN** the caller passes an object without `level`
- **THEN** schema validation metadata MUST include `filters.level` in
  `missing_required`.

### Requirement: Runtime Contract Schema Validation Posture

The system MUST describe the supported schema validation subset in the tool
runtime contract.

#### Scenario: Runtime contract is built

- **WHEN** `ToolRuntimeService.build_runtime_contract()` is called
- **THEN** `execution_adapter.schema_validation` MUST identify
  `lightweight_schema_v1`
- **AND** the supported keywords MUST include `type`, `enum`, and
  `object.required`.
