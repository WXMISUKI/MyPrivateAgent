## ADDED Requirements

### Requirement: Multi-turn eval scenarios are deterministic contracts
The system SHALL define a lightweight multi-turn scenario format that can be evaluated without invoking a live model.

#### Scenario: Scenario contains required fields
- **GIVEN** a scenario file with `id`, `turns`, `evidence`, and `assertions`
- **WHEN** the evaluator loads the scenario
- **THEN** it can produce a compact report with scenario id, status, assertion results, and execution mode

#### Scenario: Scenario is disabled
- **GIVEN** a scenario has `enabled=false`
- **WHEN** the evaluator runs it
- **THEN** the scenario result is `skipped`
- **AND** no assertions are treated as failed

### Requirement: Eval gate validates grounding, prompt, memory, tool, and response expectations
The evaluator SHALL support deterministic assertions over control-plane evidence blocks.

#### Scenario: Grounding no-evidence fallback is asserted
- **GIVEN** scenario evidence says grounding requires citations and evidence is unavailable
- **WHEN** assertions require `response_behavior=refuse_or_clarify`
- **THEN** the evaluator passes only when the evidence response behavior matches the expected fallback

#### Scenario: PromptOps version visibility is asserted
- **GIVEN** scenario evidence includes prompt key, version, and status
- **WHEN** assertions require the same prompt key, version, and status
- **THEN** the evaluator records the prompt assertion as passed

#### Scenario: MemoryOps boundary is asserted
- **GIVEN** scenario evidence includes a conversation summary and retrieved knowledge posture
- **WHEN** assertions require retrieved evidence not to be stored as long-term memory by default
- **THEN** the evaluator passes only when the evidence keeps retrieved knowledge promotion explicit

### Requirement: Eval gate reports blocked malformed scenarios
The evaluator SHALL return `blocked` for malformed or incomplete scenarios instead of changing runtime behavior.

#### Scenario: Scenario has no turns
- **GIVEN** a scenario has no user/assistant turns
- **WHEN** the evaluator runs it
- **THEN** the scenario result is `blocked`
- **AND** the blocked reason is machine-readable

### Requirement: Eval gate does not change chat behavior
The multi-turn eval gate SHALL be side-effect-free and SHALL NOT change default chat execution, prompt injection, memory injection, tool execution, or retrieval behavior.

#### Scenario: Eval gate is run
- **WHEN** a caller runs the deterministic eval gate
- **THEN** no chat request is sent
- **AND** no prompt, memory, retrieval source, or tool state is mutated
