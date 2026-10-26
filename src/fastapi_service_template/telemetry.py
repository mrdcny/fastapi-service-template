"""OpenTelemetry setup: traces exported over OTLP, metrics scraped by Prometheus.

Configuration follows the OTel spec's environment variables rather than app settings:
``OTEL_EXPORTER_OTLP_ENDPOINT`` turns on trace export, ``OTEL_TRACES_SAMPLER`` /
``OTEL_TRACES_SAMPLER_ARG`` control sampling and ``OTEL_RESOURCE_ATTRIBUTES`` adds
resource attributes. Without an endpoint, spans are still created (so log lines get
trace ids) but nothing is exported.
"""

import os
from dataclasses import dataclass

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from fastapi_service_template import __version__
from fastapi_service_template.config import Settings

_OTLP_ENDPOINT_VARS = ("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")


@dataclass(frozen=True)
class Telemetry:
    tracer_provider: TracerProvider
    meter_provider: MeterProvider


_telemetry: Telemetry | None = None


def setup_telemetry(settings: Settings) -> Telemetry:
    """Create and register the global providers. Idempotent: OTel globals can be set once."""
    global _telemetry  # noqa: PLW0603
    if _telemetry is not None:
        return _telemetry

    resource = Resource.create(
        {
            SERVICE_NAME: settings.service_name,
            SERVICE_VERSION: __version__,
            "deployment.environment.name": settings.environment,
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    if any(os.environ.get(var) for var in _OTLP_ENDPOINT_VARS):
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(resource=resource, metric_readers=[PrometheusMetricReader()])
    metrics.set_meter_provider(meter_provider)

    _telemetry = Telemetry(tracer_provider=tracer_provider, meter_provider=meter_provider)
    return _telemetry
