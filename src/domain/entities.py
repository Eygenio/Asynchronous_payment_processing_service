from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.core.enums import Currency, OutboxStatus, PaymentStatus, WebhookDeliveryStatus


@dataclass(slots=True)
class Payment:
    amount: Decimal
    currency: Currency
    idempotency_key: str
    payment_id: UUID | None = None
    description: str | None = None
    metadata_: dict[str, Any] = field(default_factory=dict)
    status: PaymentStatus = PaymentStatus.PENDING
    webhook_url: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None


@dataclass(slots=True)
class Outbox:
    event_type: str
    payload: dict[str, Any]
    id: UUID | None = None
    status: OutboxStatus = OutboxStatus.PENDING
    retry_count: int = 0
    backoff_delay: datetime | None = None
    locked_until: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class WebhookOutbox:
    payment_id: UUID
    target_url: str
    payload: dict[str, Any]
    id: UUID | None = None
    status: WebhookDeliveryStatus = WebhookDeliveryStatus.PENDING
    retry_count: int = 0
    next_attempt_at: datetime | None = None
    locked_until: datetime | None = None
    last_error: str | None = None
    created_at: datetime | None = None
    delivered_at: datetime | None = None
