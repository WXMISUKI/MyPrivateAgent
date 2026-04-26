# Demo Storage Architecture Plan

## Goal

Make the agent framework demo runnable by default without external database infrastructure, while keeping external database support as an optional deployment mode.

## Recommended Default

For demo and local development:

- runtime state in memory
- persistence in local SQLite
- config and instructions in local files
- external MySQL/PostgreSQL only when a real application needs multi-user or infra-level persistence

## Why This Matches Mature Agents

Publicly documented mature agent tools typically favor local/project-level configuration and state before external databases:

- Claude Code:
  - local/user/project settings files
  - `CLAUDE.md`
  - project-local agent definitions
- OpenAI Codex CLI:
  - local config
  - local state database
- Gemini CLI:
  - local settings files

The common pattern is not “everything in memory” and not “external database by default”, but:

1. in-memory runtime state
2. local durable storage
3. optional external persistence

## Current Project Direction

### Phase S1: SQLite By Default

Implemented:

- `backend/config.py`
  - introduces `DB_MODE`
  - defaults to `sqlite`
  - builds `DATABASE_URL` automatically
- `backend/database.py`
  - uses SQLite locally by default
  - creates local data directory automatically
- `backend/agent_server/bootstrap.py`
  - only runs MySQL database creation flow when `DB_MODE=mysql`
  - otherwise initializes local SQLite storage directly
- `backend/services/startup_diagnostics_service.py`
  - surfaces storage mode and actual connection target

## Recommended Next Steps

1. Keep SQLite as the default demo store.
2. Gradually separate storage adapters behind service/repository interfaces.
3. Move selected demo-friendly state from SQL tables to optional file-based stores only if that meaningfully reduces complexity.
4. Keep MySQL as an explicit opt-in mode for real deployments, not the default demo path.
