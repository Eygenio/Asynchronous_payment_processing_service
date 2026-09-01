from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

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

from src.application.services.outbox import OutboxService
from src.config.settings import settings
from src.infrastructure.models.base import ModelBase
from src.infrastructure.repositories.outbox import OutboxRepository
from src.infrastructure.repositories.payments import PaymentRepository
from src.infrastructure.repositories.webhook_outbox import WebhookOutboxRepository
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork


def _sync_db_connection(database: str):
    return psycopg2.connect(
        host=settings.db.host,
        port=settings.db.port,
        user=settings.db.user,
        password=settings.db.password,
        dbname=database,
    )


def _create_database() -> None:
    connection = _sync_db_connection("postgres")

    try:
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM pg_database
                WHERE datname = %s
                """,
                (settings.test_db_name,),
            )

            database_exists = cursor.fetchone() is not None

            if not database_exists:
                cursor.execute(f'CREATE DATABASE "{settings.test_db_name}"')
    finally:
        connection.close()


def _drop_database() -> None:
    connection = _sync_db_connection("postgres")

    try:
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM pg_database
                WHERE datname = %s
                """,
                (settings.test_db_name,),
            )

            database_exists = cursor.fetchone() is not None

            if not database_exists:
                return

            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid()
                """,
                (settings.test_db_name,),
            )

            cursor.execute(f'DROP DATABASE "{settings.test_db_name}"')
    finally:
        connection.close()


def _database_url() -> str:
    return (
        f"{settings.db.driver_name}://"
        f"{settings.db.user}:{settings.db.password}@"
        f"{settings.db.host}:{settings.db.port}/{settings.test_db_name}"
    )


@pytest.fixture(scope="session")
def integration_database() -> str:
    _create_database()

    try:
        yield settings.test_db_name
    finally:
        _drop_database()


@pytest.fixture(scope="session")
async def integration_engine(
    integration_database: str,
) -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(
        _database_url(),
        poolclass=NullPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(ModelBase.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def integration_session(
    integration_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(
        integration_engine,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with integration_engine.begin() as connection:
        for table in reversed(ModelBase.metadata.sorted_tables):
            await connection.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))


@pytest.fixture
def integration_session_factory(
    integration_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        integration_engine,
        expire_on_commit=False,
    )


@pytest.fixture
def integration_uow(
    integration_session: AsyncSession,
) -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(integration_session)


@pytest.fixture
def payment_repository(
    integration_session: AsyncSession,
) -> PaymentRepository:
    return PaymentRepository(integration_session)


@pytest.fixture
def outbox_repository(
    integration_session: AsyncSession,
) -> OutboxRepository:
    return OutboxRepository(integration_session)


@pytest.fixture
def webhook_repository(
    integration_session: AsyncSession,
) -> WebhookOutboxRepository:
    return WebhookOutboxRepository(integration_session)


@pytest.fixture
def outbox_publisher() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def outbox_dlq_publisher() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def outbox_service(
    integration_uow: SQLAlchemyUnitOfWork,
    integration_session_factory: async_sessionmaker[AsyncSession],
    outbox_publisher: AsyncMock,
    outbox_dlq_publisher: AsyncMock,
) -> OutboxService:
    return OutboxService(
        integration_uow,
        session_factory=integration_session_factory,
        publisher=outbox_publisher,
        dlq_publisher=outbox_dlq_publisher,
    )
