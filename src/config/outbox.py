from pydantic import BaseModel


class OutboxConfig(BaseModel):
    base_retry_delay_seconds: int
    max_attempts: int
    max_consumer_retries: int
