from pydantic import BaseModel, Field


class PaymentConfig(BaseModel):
    exchange_name: str = "payments"
    dlx_name: str = "payments.dlx"
    new_route: str = "payments.new"
    retry_route: str = "payments.new.retry"
    dlq_route: str = "payments.new.dlq"
    retry_delay_ms: int = Field(default=10_000, ge=100)
    new_topic: str = "payments.new"
