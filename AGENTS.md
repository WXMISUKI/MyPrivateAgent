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
