"""Typed configuration loaded from environment variables (12-factor).

Every setting is read from an ``APP_``-prefixed variable, e.g. ``APP_LOG_LEVEL=DEBUG``.
OpenTelemetry is configured separately through the standard ``OTEL_*`` variables
(see docs/adr/0005-opentelemetry.md), so it works the same as in any other OTel service.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "dev", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    service_name: str = "fastapi-service-template"
    environment: Environment = "local"

    host: str = "0.0.0.0"  # noqa: S104 - containers must listen on all interfaces
    port: int = Field(default=8000, ge=1, le=65535)

    log_level: LogLevel = "INFO"
    log_json: bool = True

    # SecretStr keeps the password out of reprs, logs and tracebacks.
    database_url: SecretStr = SecretStr("postgresql+asyncpg://app:app@localhost:5432/app")
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    db_connect_timeout_seconds: float = Field(default=5.0, gt=0)

    readiness_timeout_seconds: float = Field(default=2.0, gt=0)
    # Must stay below the pod's terminationGracePeriodSeconds minus the preStop sleep.
    shutdown_timeout_seconds: int = Field(default=20, ge=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
