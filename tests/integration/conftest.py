import os
from collections.abc import AsyncGenerator
from contextlib import suppress

import psycopg2
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.infrastructure.models.base import ModelBase
from src.infrastructure.repositories.outbox import OutboxRepository
from src.infrastructure.repositories.payments import PaymentRepository
from src.infrastructure.repositories.webhook_outbox import WebhookOutboxRepository
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork

TEST_DB_NAME = os.getenv("TEST_DB__NAME", "payments_test")
DB_HOST = os.getenv("TEST_DB__HOST", os.getenv("DB__HOST", "localhost"))
DB_PORT = int(os.getenv("TEST_DB__PORT", os.getenv("DB__PORT", "5432")))
DB_USER = os.getenv("TEST_DB__USER", os.getenv("DB__USER", "postgres"))
DB_PASSWORD = os.getenv("TEST_DB__PASSWORD", os.getenv("DB__PASSWORD", "postgres"))


def _sync_db_connection(dbname: str):
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=dbname,
    )


def _create_database() -> None:
    with _sync_db_connection("postgres") as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')


def _drop_database() -> None:
    with _sync_db_connection("postgres") as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f'REVOKE CONNECT ON DATABASE "{TEST_DB_NAME}" FROM public')
            cursor.execute(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                (TEST_DB_NAME,),
            )
            cursor.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')


def _database_url() -> str:
    return f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"


@pytest.fixture(scope="session")
def integration_database() -> str:
    with suppress(psycopg2.errors.DuplicateDatabase):
        _create_database()
    try:
        yield TEST_DB_NAME
    finally:
        _drop_database()


@pytest.fixture(scope="session")
async def integration_engine(integration_database: str) -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(_database_url(), poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(ModelBase.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def integration_session(
    integration_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(integration_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with integration_engine.begin() as connection:
        for table in reversed(ModelBase.metadata.sorted_tables):
            await connection.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))


@pytest.fixture
def integration_session_factory(
    integration_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(integration_engine, expire_on_commit=False)


@pytest.fixture
def integration_uow(integration_session: AsyncSession) -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(integration_session)


@pytest.fixture
def payment_repository(integration_session: AsyncSession) -> PaymentRepository:
    return PaymentRepository(integration_session)


@pytest.fixture
def outbox_repository(integration_session: AsyncSession) -> OutboxRepository:
    return OutboxRepository(integration_session)


@pytest.fixture
def webhook_repository(integration_session: AsyncSession) -> WebhookOutboxRepository:
    return WebhookOutboxRepository(integration_session)
