# durable-chat-context-compact Specification

## Purpose
Define durable compact summaries and manual compact behavior for main chat conversations.

## Requirements
### Requirement: Compact summary MUST be durable
The system SHALL persist compact summaries for main chat conversations without deleting or rewriting original message rows.

#### Scenario: Manual compact persists summary
- **WHEN** a user manually compacts an owned conversation
- **THEN** the system stores a compact summary with conversation id, summary text, covered message count, last covered message id, trigger, and timestamp

#### Scenario: Original messages remain available
- **WHEN** compact completes
- **THEN** existing conversation messages remain unchanged for audit, display, and search

### Requirement: Manual compact MUST be available through API and chat command
The system SHALL expose a manual compact operation through an authenticated backend API and a `/compact` chat command.

#### Scenario: API compact
- **WHEN** an authenticated user calls the compact endpoint for an owned conversation
- **THEN** the system creates a compact summary and returns compact metadata

#### Scenario: Slash command compact
- **WHEN** an authenticated user sends `/compact` in a chat conversation
- **THEN** the system runs compact and returns a confirmation without invoking the model orchestrator

### Requirement: Context packing MUST consume latest durable summary
The system MUST use the latest durable compact summary when assembling model input for main chat.

#### Scenario: Summary and post-summary messages are packed
- **WHEN** a conversation has a durable summary and newer messages after the summary boundary
- **THEN** model input contains the durable summary and recent newer messages before the current user message

#### Scenario: No durable summary exists
- **WHEN** a conversation has no durable summary
- **THEN** model input falls back to deterministic transient summary and recent-message packing

### Requirement: Durable summaries can be represented in MemoryOps
Durable chat compact summaries SHALL be representable as `conversation_summary` entries in the MemoryOps lifecycle registry without changing compact behavior.

#### Scenario: Summary maps to MemoryOps entry
- **WHEN** a latest durable conversation summary is available
- **THEN** MemoryOps can expose its `conversation_id`, `message_count`, `last_message_id`, `trigger`, and `created_at`
- **AND** compact summary persistence and context packing behavior remain unchanged
