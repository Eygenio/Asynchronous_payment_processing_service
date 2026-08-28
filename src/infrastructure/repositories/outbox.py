from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Outbox
from src.domain.repositories import IOutboxRepository
from src.core.enums import OutboxStatus
from src.infrastructure.models.outbox import OutboxOrm


class OutboxRepository(IOutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: OutboxOrm) -> Outbox:
        return Outbox(
            id=orm.id,
            event_type=orm.event_type,
            payload=orm.payload,
            status=orm.status,
            retry_count=orm.retry_count,
            backoff_delay=orm.backoff_delay,
            published_at=orm.published_at,
            created_at=orm.created_at,
        )

    async def add(self, outbox: Outbox) -> Outbox:
        orm = OutboxOrm(
            event_type=outbox.event_type,
            payload=outbox.payload,
            status=outbox.status,
        )
        self._session.add(orm)
        await self._session.flush()
        outbox.id = orm.id
        outbox.created_at = orm.created_at
        return outbox

    async def get_ready_for_dispatch(self, limit: int) -> list[Outbox]:
        statement = (
            select(OutboxOrm)
            .where(OutboxOrm.status == OutboxStatus.PENDING)
            .where(
                or_(
                    OutboxOrm.backoff_delay.is_(None),
                    OutboxOrm.backoff_delay <= datetime.now(UTC),
                )
            )
            .order_by(OutboxOrm.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(statement)
        orm_list = result.scalars().all()
        return [self._to_domain(orm) for orm in orm_list]

    async def mark_published(self, message: Outbox) -> None:
        if message.id is None:
            raise ValueError("message id is None")
        orm = await self._session.get(OutboxOrm, message.id)
        if orm:
            orm.status = OutboxStatus.PUBLISHED
            orm.published_at = datetime.now(UTC)
            orm.backoff_delay = None

    async def schedule_retry(
        self,
        message: Outbox,
        attempts: int,
        next_retry_at: datetime,
    ) -> None:
        if message.id is None:
            raise ValueError("message id is None")
        orm = await self._session.get(OutboxOrm, message.id)
        if orm:
            orm.retry_count = attempts
            orm.backoff_delay = next_retry_at

    async def mark_failed(self, message: Outbox, attempts: int) -> None:
        if message.id is None:
            raise ValueError("message id is None")
        orm = await self._session.get(OutboxOrm, message.id)
        if orm:
            orm.status = OutboxStatus.FAILED
            orm.retry_count = attempts
            orm.backoff_delay = None
