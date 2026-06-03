# Repository Guidelines

## Project Structure & Module Organization
`backend/` contains the FastAPI app, database models, orchestration logic, and API routers. Start in `backend/main.py`, then trace route handlers under `backend/routers/` and shared services in files such as `orchestrator.py` and `learning_recorder.py`.

`frontend-vue/` is the active Vue 3 + Vite client. Views live in `src/views/`, reusable UI in `src/components/`, state in `src/stores/`, and API helpers in `src/api/` and `src/services/`. `skill_store/dev-browser/` is an isolated TypeScript skill package with its own tests. `docs/` and `问题记录/` hold design notes and troubleshooting records.

## Build, Test, and Development Commands
Backend setup and run:
```powershell
cd D:\AI\AIcode\MyPrivateAgent
pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```
Use `python -m backend.main` for a simpler local start.

Vue frontend:
```powershell
cd frontend-vue
npm install
npm run dev
npm run build
```
`npm run build` verifies the production bundle.

Skill package:
```powershell
cd skill_store/dev-browser
npm install
npm run test
```

## Coding Style & Naming Conventions
Follow the existing style in each module: Python uses 4-space indentation, snake_case functions, and descriptive module names; Vue SFCs use PascalCase component files such as `AppHeader.vue`; JS store and service files use lower-case names such as `auth.js` and `commands.js`; TypeScript in `skill_store/dev-browser` uses 2-space indentation and ES modules.

Keep changes scoped to the module you are touching. Reuse existing router, store, and service patterns before adding new abstractions.

## Testing Guidelines
Automated tests currently live in `skill_store/dev-browser/src/snapshot/__tests__/` and run with Vitest. Name new tests `*.test.ts`. For backend and `frontend-vue`, there is no established suite yet, so add focused tests when introducing reusable logic and document manual verification steps in your change.

## Commit & Pull Request Guidelines
Git history uses short Conventional Commit-style subjects, for example `feat: ...`. Prefer `feat:`, `fix:`, `refactor:`, and `docs:` prefixes. Keep each commit focused.

Pull requests should include a clear summary, impacted areas (`backend`, `frontend-vue`, `skill_store`), setup or migration notes, and screenshots for UI changes. Link related issues or design notes when relevant.

## Security & Configuration Tips
Secrets live in the repository root `.env`; do not hardcode credentials or API keys. The backend expects local services such as MySQL and model providers to be configured before running chat flows.

<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`codegraph_*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

### When to prefer CodeGraph over native search

Use CodeGraph for structural questions: what calls what, what would break, where a symbol is defined, or what a signature looks like. Use native grep/read only for literal text queries, comments, log messages, or after a specific file has already been identified.

| Question | Tool |
|---|---|
| Where is X defined? / Find symbol named X | `codegraph_search` |
| What calls function Y? | `codegraph_callers` |
| What does Y call? | `codegraph_callees` |
| What would break if I changed Z? | `codegraph_impact` |
| Show me Y's signature / source / docstring | `codegraph_node` |
| Give me focused context for a task/area | `codegraph_context` |
| See several related symbols' source at once | `codegraph_explore` |
| What files exist under path/ | `codegraph_files` |
| Is the index healthy? | `codegraph_status` |

### Rules of thumb

- Answer directly. For architecture and trace questions, start with `codegraph_context`, then use one `codegraph_explore` call for the symbols it surfaces.
- Trust CodeGraph structural results. They come from a full AST parse and should not be re-verified with grep unless the question is about literal text.
- Do not grep first when looking up a symbol by name. `codegraph_search` returns kind, location, and signature in one call.
- Do not chain `codegraph_search` plus `codegraph_node` when focused context is enough; use `codegraph_context`.
- Do not loop `codegraph_node` over many symbols; one `codegraph_explore` call returns several related symbols grouped together.
- After file edits, allow for index lag. The watcher can debounce briefly behind writes.

### If `.codegraph/` does not exist

The MCP server returns "not initialized." Ask the user: "I notice this project doesn't have CodeGraph initialized. Want me to run `codegraph init -i` to build the index?"

### CLI fallback

If the MCP tools are not exposed in the current client, use the local CLI:

```powershell
codegraph status
codegraph sync
codegraph files --max-depth 2 --no-metadata
codegraph context "<task>"
codegraph query "<symbol>"
```
<!-- CODEGRAPH_END -->
