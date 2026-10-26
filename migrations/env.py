import asyncio

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi_service_template import models  # noqa: F401 - registers tables on Base.metadata
from fastapi_service_template.config import Settings
from fastapi_service_template.db import Base
from fastapi_service_template.log import configure_logging

settings = Settings()
configure_logging(settings.log_level, json=settings.log_json)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Render SQL to stdout (``alembic upgrade head --sql``) for review or DBA hand-off."""
    context.configure(
        url=settings.database_url.get_secret_value(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.database_url.get_secret_value(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
