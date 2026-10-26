"""Operational endpoints: liveness, readiness and Prometheus metrics.

See docs/adr/0008-health-checks-and-graceful-shutdown.md for why liveness never
touches dependencies while readiness does.
"""

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, Request, Response
from opentelemetry.instrumentation.utils import suppress_instrumentation
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from sqlalchemy import text

router = APIRouter(tags=["ops"], include_in_schema=False)
log = structlog.get_logger(__name__)


@router.get("/livez")
async def livez() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request, response: Response) -> dict[str, Any]:
    checks = {"database": await _check_database(request)}
    ready = all(result == "ok" for result in checks.values())
    response.status_code = 200 if ready else 503
    return {"status": "ok" if ready else "unavailable", "checks": checks}


@router.get("/metrics")
def prometheus_metrics() -> Response:
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


async def _check_database(request: Request) -> str:
    timeout = request.app.state.settings.readiness_timeout_seconds
    try:
        # Probes run every few seconds; their queries would otherwise become root traces.
        with suppress_instrumentation():
            async with asyncio.timeout(timeout), request.app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
    except Exception as exc:  # any failure means "not ready"
        log.warning("readiness check failed", check="database", error=repr(exc))
        return "fail"
    return "ok"
