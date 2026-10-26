# 5. OpenTelemetry for traces and metrics

- Status: accepted
- Date: 2026-10-26

## Context

We need request tracing across services and RED metrics (rate, errors, duration), without tying the code to a vendor.

## Decision

Instrument with **OpenTelemetry**:

- **Traces** export over OTLP/HTTP. FastAPI and SQLAlchemy are auto-instrumented, so each request shows its database queries as child spans.
- **Metrics** use the OTel API and are exposed at `/metrics` in **Prometheus** format for scraping. Prometheus scraping is the most common setup in Kubernetes and needs no extra collector.
- Configuration uses the **standard `OTEL_*` environment variables** (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES_SAMPLER`, `OTEL_RESOURCE_ATTRIBUTES`), not app-specific settings, so platform teams configure this service like any other OTel service.
- With no endpoint set, spans are still created (so logs have trace ids) but not exported.

## Consequences

- Switching backends (Jaeger, Tempo, Honeycomb, Datadog) is a config change.
- Pushing metrics over OTLP instead of scraping would mean swapping the Prometheus reader for an OTLP metric exporter in `telemetry.py`.
- OTel providers are process globals and can only be set once, so `setup_telemetry` is idempotent.
- `/livez`, `/readyz` and `/metrics` are excluded from tracing so probes don't flood the trace store.
