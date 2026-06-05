## ADDED Requirements

### Requirement: Multi-turn eval follows MemoryOps before behavior promotion
The provider capability roadmap SHALL route prompt/RAG/context behavior promotion through a multi-turn eval gate after Grounding Policy, PromptOps, and MemoryOps contracts are visible.

#### Scenario: Internal control contracts are complete
- **WHEN** grounding policy, PromptOps, and MemoryOps visibility contracts are available
- **THEN** the next internal control-plane slice SHOULD be `add-multiturn-agent-evaluation-gate`
- **AND** default chat retrieval injection, prompt rollout, or memory injection promotion SHOULD remain blocked until representative scenarios pass
