# promptops-versioned-prompt-contract Specification

## Purpose
Define the minimal versioned PromptOps read model used to expose existing system prompts as governance-visible contracts without changing runtime prompt injection.

## Requirements
### Requirement: Existing prompts expose versioned PromptOps contracts
The system SHALL expose existing prompt records as versioned PromptOps contracts without requiring a database migration.

#### Scenario: Legacy prompt is normalized
- **GIVEN** a `SystemPrompt` record with `prompt_key`, `prompt_type`, `content`, and `is_active=true`
- **WHEN** the PromptOps contract is built
- **THEN** the prompt contract includes `prompt_key`, `version`, `status`, `template`, `variables_schema`, and `runtime_binding`
- **AND** `version` defaults to `"1"`
- **AND** `status` defaults to `"active"`

#### Scenario: Inactive prompt is archived in the read model
- **GIVEN** a `SystemPrompt` record with `is_active=false`
- **WHEN** the PromptOps contract is built
- **THEN** the prompt contract reports `status="archived"` unless an explicit draft or review status tag is present
- **AND** runtime injection behavior remains unchanged

### Requirement: PromptOps contracts expose governance metadata
The PromptOps contract SHALL preserve lightweight governance metadata needed by later eval, grounding, rollout, and rollback changes.

#### Scenario: Prompt tags include governance metadata
- **GIVEN** a prompt has tags such as `version:2`, `status:review`, `owner:agent-team`, `grounding_policy:ecommerce`, `eval_set:refund-eval`, `approval:pending`, and `rollback_target:1`
- **WHEN** the PromptOps contract is built
- **THEN** the contract includes those values in bounded fields
- **AND** unknown tags remain available in the raw `tags` field

#### Scenario: Prompt template contains variables
- **GIVEN** a prompt template contains `{{customer_id}}` and `{{order_id}}`
- **WHEN** the PromptOps contract is built
- **THEN** `variables_schema.properties` includes `customer_id` and `order_id`
- **AND** both variables are included in `variables_schema.required`

### Requirement: PromptOps visibility does not change chat behavior
The PromptOps contract SHALL be read-only and SHALL NOT change default chat prompt injection, prompt activation, or retrieval behavior.

#### Scenario: PromptOps registry is requested
- **WHEN** a caller reads the PromptOps contract registry
- **THEN** the response includes the contract version, prompt count, active prompt count, and prompt contracts
- **AND** no prompt is activated, deactivated, rendered, or injected as a side effect
