from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import async_sessionmaker

from fastapi_service_template import __version__
from fastapi_service_template.api import notes, ops
from fastapi_service_template.config import Settings, get_settings
from fastapi_service_template.db import create_engine
from fastapi_service_template.log import configure_logging
from fastapi_service_template.middleware import AccessLogMiddleware
from fastapi_service_template.telemetry import setup_telemetry

log = structlog.get_logger(__name__)

OPS_PATHS = frozenset({"/livez", "/readyz", "/metrics"})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    telemetry = setup_telemetry(settings)

    engine = create_engine(settings)
    sqlalchemy_instrumentor = SQLAlchemyInstrumentor()
    sqlalchemy_instrumentor.instrument(
        engine=engine.sync_engine, tracer_provider=telemetry.tracer_provider
    )
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    log.info("service started", version=__version__, environment=settings.environment)

    yield

    # uvicorn has stopped accepting connections and drained in-flight requests by now.
    log.info("service stopping")
    await engine.dispose()
    sqlalchemy_instrumentor.uninstrument()
    telemetry.tracer_provider.force_flush()
    log.info("service stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, json=settings.log_json)
    telemetry = setup_telemetry(settings)

    app = FastAPI(title=settings.service_name, version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.include_router(ops.router)
    app.include_router(notes.router)

    # Added before instrumentation so the OTel middleware wraps it and access logs carry trace ids.
    app.add_middleware(AccessLogMiddleware, skip_paths=OPS_PATHS)
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=telemetry.tracer_provider,
        meter_provider=telemetry.meter_provider,
        excluded_urls=",".join(OPS_PATHS),
    )
    return app
