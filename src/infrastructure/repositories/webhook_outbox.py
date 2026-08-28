from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import WebhookDeliveryStatus
from src.domain.entities import WebhookOutbox
from src.infrastructure.models.webhook_outbox import WebhookOutboxOrm


class WebhookOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: WebhookOutboxOrm) -> WebhookOutbox:
        return WebhookOutbox(
            payment_id=orm.payment_id,
            target_url=orm.target_url,
            payload=orm.payload,
            id=orm.id,
            status=orm.status,
            retry_count=orm.retry_count,
            next_attempt_at=orm.next_attempt_at,
            locked_until=orm.locked_until,
            last_error=orm.last_error,
            created_at=orm.created_at,
            delivered_at=orm.delivered_at,
        )

    async def add(self, delivery: WebhookOutbox) -> WebhookOutbox:
        orm = WebhookOutboxOrm(
            payment_id=delivery.payment_id,
            target_url=delivery.target_url,
            payload=delivery.payload,
            status=delivery.status,
            retry_count=delivery.retry_count,
        )
        self._session.add(orm)
        await self._session.flush()
        delivery.id = orm.id
        delivery.created_at = orm.created_at
        return delivery

    async def claim_ready(self, limit: int, lease_until: datetime) -> list[WebhookOutbox]:
        now = datetime.now(UTC)
        statement = (
            select(WebhookOutboxOrm)
            .where(
                or_(
                    WebhookOutboxOrm.status == WebhookDeliveryStatus.PENDING,
                    (
                        (WebhookOutboxOrm.status == WebhookDeliveryStatus.PROCESSING)
                        & (WebhookOutboxOrm.locked_until < now)
                    ),
                )
            )
            .where(
                or_(
                    WebhookOutboxOrm.next_attempt_at.is_(None),
                    WebhookOutboxOrm.next_attempt_at <= now,
                )
            )
            .order_by(WebhookOutboxOrm.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(statement)
        rows = list(result.scalars().all())
        for row in rows:
            row.status = WebhookDeliveryStatus.PROCESSING
            row.locked_until = lease_until
        await self._session.flush()
        return [self._to_domain(row) for row in rows]

    async def mark_delivered(self, delivery: WebhookOutbox) -> None:
        if delivery.id is None:
            raise ValueError("webhook delivery id is None")
        orm = await self._session.get(WebhookOutboxOrm, delivery.id)
        if orm:
            orm.status = WebhookDeliveryStatus.DELIVERED
            orm.locked_until = None
            orm.next_attempt_at = None
            orm.last_error = None
            orm.delivered_at = datetime.now(UTC)

    async def schedule_retry(
        self,
        delivery: WebhookOutbox,
        attempts: int,
        next_attempt_at: datetime,
        error: str,
    ) -> None:
        if delivery.id is None:
            raise ValueError("webhook delivery id is None")
        orm = await self._session.get(WebhookOutboxOrm, delivery.id)
        if orm:
            orm.status = WebhookDeliveryStatus.PENDING
            orm.retry_count = attempts
            orm.next_attempt_at = next_attempt_at
            orm.locked_until = None
            orm.last_error = error[:4000]

    async def mark_failed(
        self,
        delivery: WebhookOutbox,
        attempts: int,
        error: str,
    ) -> None:
        if delivery.id is None:
            raise ValueError("webhook delivery id is None")
        orm = await self._session.get(WebhookOutboxOrm, delivery.id)
        if orm:
            orm.status = WebhookDeliveryStatus.FAILED
            orm.retry_count = attempts
            orm.next_attempt_at = None
            orm.locked_until = None
            orm.last_error = error[:4000]
