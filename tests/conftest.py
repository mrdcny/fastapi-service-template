import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi_service_template.config import Settings
from fastapi_service_template.main import create_app

ROOT = Path(__file__).resolve().parent.parent
# Port 1 refuses connections immediately, so readiness fails fast without a database.
UNREACHABLE_DB = "postgresql+asyncpg://app:app@127.0.0.1:1/app"


def make_settings(database_url: str) -> Settings:
    return Settings(
        environment="test",
        log_json=False,
        database_url=database_url,
        db_connect_timeout_seconds=1,
        readiness_timeout_seconds=1,
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """App wired to a database that does not exist. Enough for everything but data tests."""
    with TestClient(create_app(make_settings(UNREACHABLE_DB))) as c:
        yield c


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    os.environ["APP_DATABASE_URL"] = url  # read by migrations/env.py
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    return url


@pytest.fixture
def db_client(database_url: str) -> Iterator[TestClient]:
    with TestClient(create_app(make_settings(database_url))) as c:
        yield c
    asyncio.run(_truncate(database_url))


async def _truncate(database_url: str) -> None:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE notes"))
    await engine.dispose()
