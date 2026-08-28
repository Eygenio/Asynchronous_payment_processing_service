from pydantic import BaseModel


class PaymentConfig(BaseModel):
    exchange_name: str
    dlx_name: str
    new_route: str
    retry_route: str
    dlq_route: str
    retry_delay_ms: int
    new_topic: str
