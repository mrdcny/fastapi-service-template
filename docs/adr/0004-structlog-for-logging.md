# 4. structlog for structured logging

- Status: accepted
- Date: 2026-10-26

## Context

Logs are read mostly by machines (Loki, CloudWatch, Datadog) and searched by field, so they should be JSON, one object per line. Locally, people need to read them. Third-party libraries (uvicorn, SQLAlchemy, alembic) log through the standard library, and their lines must come out in the same format. Every line should carry the trace id so logs and traces can be joined.

Options: stdlib `logging` with a JSON formatter, `loguru`, `structlog`.

## Decision

Use **structlog**, rendering through the stdlib `logging` handler (`ProcessorFormatter`).

- Context binds as key/value pairs (`log.info("note created", note_id=...)`) rather than being formatted into the message, so it's queryable.
- The same processor chain renders our logs and stdlib logs, so there's one consistent stream.
- A small processor adds `trace_id` and `span_id` from the active OpenTelemetry span.
- `APP_LOG_JSON=false` switches to coloured console output for local development, with no code change.

`loguru` is pleasant but replaces stdlib logging rather than integrating with it, which makes routing library logs awkward. Plain stdlib with a JSON formatter works, but binding context per request is clumsy.

## Consequences

- We emit our own access log from middleware and disable uvicorn's, so access lines are structured too and include the trace id.
- Probe and `/metrics` requests aren't access-logged, to keep the volume down.
