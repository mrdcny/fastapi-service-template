"""Entry point: ``python -m fastapi_service_template``.

uvicorn handles SIGTERM: it stops accepting connections, waits up to
``shutdown_timeout_seconds`` for in-flight requests, then runs the lifespan shutdown.
"""

import uvicorn

from fastapi_service_template.config import get_settings
from fastapi_service_template.main import create_app


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_config=None,  # keep the structlog configuration from create_app
        access_log=False,
        server_header=False,
        timeout_graceful_shutdown=settings.shutdown_timeout_seconds,
    )


if __name__ == "__main__":
    main()
