# 2. Python with FastAPI on uvicorn

- Status: accepted
- Date: 2026-10-26

## Context

The service needs an async HTTP framework with typed request/response models, generated OpenAPI docs, and good OpenTelemetry support. Candidates: FastAPI, Litestar, Flask (sync), Django (heavier, batteries we don't need).

## Decision

Use **FastAPI** served by **uvicorn**, with Pydantic v2 models at the API boundary and the app built by a `create_app(settings)` factory.

- FastAPI has the widest adoption, so it's what most teams already know and what most libraries integrate with first.
- Pydantic gives runtime validation and static types from one definition, and the same library handles configuration (`pydantic-settings`).
- `opentelemetry-instrumentation-fastapi` is maintained upstream.
- The factory makes tests build an app per test with its own settings, with no global state to patch.

Litestar was a close second (faster, more structured), but its smaller ecosystem outweighs that for a template meant to be copied.

## Consequences

- Async throughout: handlers must not block. Database access uses SQLAlchemy's asyncio API with asyncpg.
- One uvicorn worker per container. We scale by adding pods rather than in-process workers, which keeps metrics, signals and memory limits simple.
