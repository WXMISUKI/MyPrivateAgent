# agent-grounding-policy Specification

## MODIFIED Requirements

### Requirement: Grounding decision gate is side-effect-free
The system SHALL expose a deterministic grounding policy decision gate that does not invoke retrieval or mutate chat behavior.

#### Scenario: Default chat remains disabled
- **WHEN** no domain-agent grounding decision is requested
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** no provider retrieval, prompt injection, memory injection, or context packing behavior changes

#### Scenario: Agent policy is missing
- **WHEN** a grounding decision is requested for an unknown agent or an agent without declared grounding policy
- **THEN** the decision is `blocked` or `review`
- **AND** the output includes a machine-readable reason code

#### Scenario: Trial surface evaluates grounding decision
- **WHEN** the grounded-answer trial surface receives a caller-supplied evidence pack
- **THEN** it may evaluate the grounding decision for that evidence pack
- **AND** this does not invoke retrieval, mutate chat state, or compose an answer
