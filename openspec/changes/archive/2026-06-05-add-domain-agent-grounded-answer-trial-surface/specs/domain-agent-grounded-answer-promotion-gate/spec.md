# domain-agent-grounded-answer-promotion-gate Specification

## MODIFIED Requirements

### Requirement: Promotion gate is side-effect-free

The promotion gate SHALL only aggregate readiness evidence and SHALL NOT invoke provider, chat, answer generation, memory writes, or source binding behavior.

#### Scenario: Promotion gate is evaluated
- **WHEN** a caller evaluates the promotion gate
- **THEN** no provider request is sent
- **AND** no answer is generated
- **AND** no memory, audit, source binding, or chat state is mutated
- **AND** default `/api/chat` retrieval injection remains disabled

#### Scenario: Trial surface consumes promotion decision
- **WHEN** the grounded-answer trial surface evaluates a requested agent
- **THEN** it consumes the promotion decision as trial evidence
- **AND** the trial surface does not promote runtime behavior or default chat retrieval injection by itself
