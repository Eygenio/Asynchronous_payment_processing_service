from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.core.enums import Currency, PaymentStatus, OutboxStatus

class Payment(BaseModel):
    payment_id: UUID | None = None
    amount: Decimal
    currency: Currency
    description: str | None = None
    metadata_: dict[str, Any] = {}
    status: PaymentStatus = PaymentStatus.PENDING
    idempotency_key: str
    webhook_url: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None

class Outbox(BaseModel):
    id: UUID | None = None
    event_type: str
    payload: dict[str, Any]
    status: OutboxStatus = OutboxStatus.PENDING
    retry_count: int = 0
    backoff_delay: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
