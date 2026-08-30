from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.core.enums import Currency, OutboxStatus, PaymentStatus
from src.domain.entities import Outbox, Payment


DEFAULT_PAYMENT_ID = UUID("12345678-1234-5678-1234-567812345678")
DEFAULT_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def payment(
    *,
    payment_id: UUID | None = DEFAULT_PAYMENT_ID,
    amount: Decimal = Decimal("100.00"),
    currency: Currency = Currency.USD,
    idempotency_key: str = "key-1",
    description: str | None = "test payment",
    metadata: dict | None = None,
    status: PaymentStatus = PaymentStatus.PENDING,
    webhook_url: str | None = None,
    created_at: datetime | None = DEFAULT_CREATED_AT,
    processed_at: datetime | None = None,
) -> Payment:
    return Payment(
        amount=amount,
        currency=currency,
        idempotency_key=idempotency_key,
        payment_id=payment_id,
        description=description,
        metadata_=metadata or {},
        status=status,
        webhook_url=webhook_url,
        created_at=created_at,
        processed_at=processed_at,
    )


def outbox(
    *,
    outbox_id: UUID | None = None,
    event_type: str = "payments.new",
    payment_id: UUID | None = None,
    status: OutboxStatus = OutboxStatus.PENDING,
    retry_count: int = 0,
) -> Outbox:
    payment_id = payment_id or uuid4()
    return Outbox(
        id=outbox_id or uuid4(),
        event_type=event_type,
        payload={"payment_id": str(payment_id)},
        status=status,
        retry_count=retry_count,
    )


def payment_payload() -> dict[str, object]:
    return {
        "amount": "100.00",
        "currency": "USD",
        "description": "Test payment",
        "metadata": {"key": "value"},
        "webhook_url": "https://example.com/webhook",
    }
