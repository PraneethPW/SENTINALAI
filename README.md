# SentinelAI

AI-Powered Intelligent Device Guardian. SentinelAI combines device telemetry, explainable risk scoring, and AI-guided security actions in a responsive SaaS workspace.

## Quick start

1. Copy `.env.example` to `.env` and set `POSTGRES_URL` and `JWT_SECRET`.
2. `docker compose up --build`
3. Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs`.

For local development, run `uvicorn app.main:app --reload` from `backend` and `npm install && npm run dev` from `frontend`.

## Architecture

- `frontend` - Vite React TypeScript client with Tailwind, motion, charts, and Three.js.
- `backend` - FastAPI service with SQLAlchemy, JWT authentication, WebSockets, and OpenRouter integration.
- `docs` - API and deployment notes.

## Notes

The app uses an SQLite database automatically when `POSTGRES_URL` is omitted, which keeps the project runnable locally. For production, use Neon PostgreSQL and apply Alembic migrations.
