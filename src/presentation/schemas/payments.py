from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.core.enums import Currency, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    currency: Currency
    description: Annotated[str | None, Field(default=None, max_length=255)]
    metadata: Annotated[dict[str, Any], Field(default_factory=dict)]
    webhook_url: HttpUrl | None = None


class PaymentCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_id: UUID
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    currency: Currency
    description: Annotated[str | None, Field(default=None, max_length=255)]
    metadata: Annotated[dict[str, Any], Field(default_factory=dict)]
    webhook_url: HttpUrl | None = None
    processed_at: datetime | None = None
