## ADDED Requirements

### Requirement: Main chat MUST include bounded persisted history
The system SHALL build main chat model input from persisted conversation messages for the active `conversation_id`, bounded by a token budget.

#### Scenario: Recent history is included
- **WHEN** a conversation has prior user and assistant messages before the current request
- **THEN** the model input includes recent prior turns before the current user message

#### Scenario: Current user message is not duplicated
- **WHEN** the current user message has already been persisted before orchestration starts
- **THEN** the model input contains that current user message exactly once

### Requirement: Older turns MUST compact into deterministic summary
The system SHALL compact older conversation turns into a deterministic system summary when the history exceeds the recent window or token budget.

#### Scenario: Older messages exceed recent window
- **WHEN** persisted history contains more turns than the configured recent history window
- **THEN** older turns are represented by a compact system summary and recent turns remain available as normal chat messages

#### Scenario: Summary does not require model invocation
- **WHEN** context packing summarizes older messages
- **THEN** the summary is generated deterministically without invoking a language model

### Requirement: Context packing MUST preserve runtime system layers
The system MUST keep runtime system prompts ahead of packed conversation history and apply conversation budget pressure after those system layers are assembled.

#### Scenario: Runtime system prompts exist
- **WHEN** capability profile, agent memory, runtime knowledge, runtime skills, or subagent role prompts are present
- **THEN** those system messages appear before packed conversation history in the model input

#### Scenario: History exceeds remaining budget
- **WHEN** conversation history cannot fit within the available budget
- **THEN** the system keeps the compact summary and newest feasible turns instead of dropping runtime system prompts
