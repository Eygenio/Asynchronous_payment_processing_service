from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import OutboxStatus
from src.domain.entities import Outbox
from src.infrastructure.models.outbox import OutboxOrm


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: OutboxOrm) -> Outbox:
        return Outbox(
            event_type=orm.event_type,
            payload=orm.payload,
            id=orm.id,
            status=orm.status,
            retry_count=orm.retry_count,
            backoff_delay=orm.backoff_delay,
            locked_until=orm.locked_until,
            published_at=orm.published_at,
            created_at=orm.created_at,
        )

    async def get_by_id(self, message_id: UUID) -> Outbox | None:
        orm = await self._session.get(OutboxOrm, message_id)
        return self._to_domain(orm) if orm else None

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

    async def claim_ready_for_dispatch(
        self,
        limit: int,
        lease_until: datetime,
    ) -> list[Outbox]:
        now = datetime.now(UTC)
        statement = (
            select(OutboxOrm)
            .where(
                or_(
                    OutboxOrm.status == OutboxStatus.PENDING,
                    (
                        (OutboxOrm.status == OutboxStatus.PROCESSING)
                        & (OutboxOrm.locked_until < now)
                    ),
                )
            )
            .where(
                or_(
                    OutboxOrm.backoff_delay.is_(None),
                    OutboxOrm.backoff_delay <= now,
                )
            )
            .order_by(OutboxOrm.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(statement)
        rows = list(result.scalars().all())
        for row in rows:
            row.status = OutboxStatus.PROCESSING
            row.locked_until = lease_until
        await self._session.flush()
        return [self._to_domain(row) for row in rows]

    async def mark_published(self, message: Outbox) -> None:
        if message.id is None:
            raise ValueError("message id is None")
        orm = await self._session.get(OutboxOrm, message.id)
        if orm:
            orm.status = OutboxStatus.PUBLISHED
            orm.published_at = datetime.now(UTC)
            orm.backoff_delay = None
            orm.locked_until = None
            orm.locked_until = None

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
            orm.status = OutboxStatus.PENDING
            orm.retry_count = attempts
            orm.backoff_delay = next_retry_at
            orm.locked_until = None

    async def mark_failed(self, message: Outbox, attempts: int) -> None:
        if message.id is None:
            raise ValueError("message id is None")
        orm = await self._session.get(OutboxOrm, message.id)
        if orm:
            orm.status = OutboxStatus.FAILED
            orm.retry_count = attempts
            orm.backoff_delay = None
