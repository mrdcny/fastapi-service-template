# fastapi-service-template

[![ci](https://github.com/OWNER/fastapi-service-template/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/fastapi-service-template/actions/workflows/ci.yml)

A production-ready template for Python HTTP services. It's what I start every new service from: everything a service needs before its first real feature, already wired up and tested, with the reasoning written down in [`docs/adr/`](docs/adr/).

## What's included

| Concern | How | Why |
| --- | --- | --- |
| Configuration | Typed `pydantic-settings`, `APP_*` env vars, secrets as `SecretStr` | [config.py](src/fastapi_service_template/config.py) |
| Logging | structlog JSON lines with `trace_id`/`span_id`, stdlib logs included | [ADR 4](docs/adr/0004-structlog-for-logging.md) |
| Tracing and metrics | OpenTelemetry: OTLP traces, Prometheus `/metrics`, FastAPI and SQLAlchemy auto-instrumented | [ADR 5](docs/adr/0005-opentelemetry.md) |
| Health | `/livez` (process only) and `/readyz` (checks dependencies) | [ADR 8](docs/adr/0008-health-checks-and-graceful-shutdown.md) |
| Graceful shutdown | preStop sleep, uvicorn drain, pool close, span flush | [ADR 8](docs/adr/0008-health-checks-and-graceful-shutdown.md) |
| Database | PostgreSQL, async SQLAlchemy 2 and asyncpg | [ADR 3](docs/adr/0003-postgres-over-mongo.md) |
| Migrations | Alembic, run as a Helm pre-upgrade Job, round-tripped in CI | [ADR 6](docs/adr/0006-migrations-as-a-release-step.md) |
| Container | Multi-stage, non-root, no build tools or source in the runtime image | [Dockerfile](Dockerfile) |
| Kubernetes | Helm chart: probes, HPA, PDB, topology spread, restricted security context | [chart](deploy/helm/fastapi-service-template) |
| CI | Lint, strict mypy, tests against real Postgres, Helm lint, image build, Trivy scan, smoke test | [ci.yml](.github/workflows/ci.yml) |

## Quick start

Needs [uv](https://docs.astral.sh/uv/) and Docker.

```bash
make install           # create .venv
cp .env.example .env
make deps              # Postgres + Jaeger in Docker
make migrate
make run               # http://localhost:8000/docs
```

Or run the whole stack, with the app in its production image:

```bash
docker compose up --build
```

Then:

```bash
curl -s localhost:8000/v1/notes -H 'content-type: application/json' -d '{"title":"hello"}'
curl -s localhost:8000/readyz
curl -s localhost:8000/metrics | grep http_server
open http://localhost:16686   # Jaeger: one trace per request, with the SQL as child spans
```

`make help` lists every target. `make check` runs what CI runs.

## How a request flows

```mermaid
flowchart LR
    client([client]) --> otel[OTel middleware<br/>starts span]
    otel --> access[access log<br/>with trace_id]
    access --> route[FastAPI route]
    route --> session[SQLAlchemy session]
    session --> pg[(PostgreSQL)]
    otel -. OTLP .-> collector[Jaeger / collector]
    prom[Prometheus] -. scrape /metrics .-> otel
```

## Layout

```
src/fastapi_service_template/
  config.py        typed settings
  log.py           structlog setup
  telemetry.py     OTel providers
  db.py, models.py SQLAlchemy engine, session dependency, models
  middleware.py    structured access log
  api/ops.py       /livez /readyz /metrics
  api/notes.py     example resource: replace with your own
  main.py          app factory and lifespan
migrations/        Alembic
deploy/helm/       Helm chart
docs/adr/          decision records
```

## Using it for a new service

1. Rename the package and `service_name`.
2. Replace `models.py` and `api/notes.py` with your domain, then run `uv run alembic revision --autogenerate -m "..."` and review the generated file.
3. Set `image.repository` in `values.yaml`.
4. Write an ADR for anything you change.

## Deploying

The chart expects an existing Secret with the database URL:

```bash
kubectl create secret generic fastapi-service-template-db \
  --from-literal=database-url='postgresql+asyncpg://user:pass@host:5432/db'
helm upgrade --install api deploy/helm/fastapi-service-template \
  --set database.existingSecret=fastapi-service-template-db \
  --set config.extraEnv[0].name=OTEL_EXPORTER_OTLP_ENDPOINT \
  --set config.extraEnv[0].value=http://otel-collector:4318
```

Helm runs the migration Job first and only rolls out new pods if it succeeds.

## Configuration

| Variable | Default | |
| --- | --- | --- |
| `APP_ENVIRONMENT` | `local` | `local`, `test`, `dev`, `staging` or `production` |
| `APP_DATABASE_URL` | local Postgres | SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `APP_LOG_LEVEL` | `INFO` | |
| `APP_LOG_JSON` | `true` | `false` for coloured console output |
| `APP_PORT` | `8000` | |
| `APP_SHUTDOWN_TIMEOUT_SECONDS` | `20` | max time to drain in-flight requests |
| `APP_READINESS_TIMEOUT_SECONDS` | `2` | per-check timeout in `/readyz` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | enables trace export |
| `OTEL_TRACES_SAMPLER` | `parentbased_always_on` | standard OTel sampling |

The full list is in [config.py](src/fastapi_service_template/config.py).

## License

MIT
