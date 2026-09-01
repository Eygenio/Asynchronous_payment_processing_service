from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.core.enums import Currency


@dataclass(frozen=True, slots=True)
class PaymentCreateDTO:
    amount: Decimal
    currency: Currency
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    webhook_url: str | None = None
