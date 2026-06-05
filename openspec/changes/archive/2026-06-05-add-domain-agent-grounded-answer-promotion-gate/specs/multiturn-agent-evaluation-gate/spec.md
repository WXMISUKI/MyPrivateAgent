# multiturn-agent-evaluation-gate Specification

## MODIFIED Requirements

### Requirement: Eval gate does not change chat behavior
The multi-turn eval gate SHALL be side-effect-free and SHALL NOT change default chat execution, prompt injection, memory injection, tool execution, or retrieval behavior.

#### Scenario: Eval gate is run
- **WHEN** a caller runs the deterministic eval gate
- **THEN** no chat request is sent
- **AND** no prompt, memory, retrieval source, or tool state is mutated

#### Scenario: Promotion gate consumes eval evidence
- **WHEN** a grounded-answer promotion gate evaluates a domain agent
- **THEN** it may consume deterministic eval report status as promotion evidence
- **AND** failed or blocked eval evidence prevents `go`
- **AND** consuming eval evidence does not run chat, models, tools, or retrieval
