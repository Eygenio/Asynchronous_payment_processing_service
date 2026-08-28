from pydantic import BaseModel, Field


class OutboxConfig(BaseModel):
    base_retry_delay_seconds: int = Field(default=3, ge=1)
    max_attempts: int = Field(default=3, ge=1)
    max_consumer_retries: int = Field(default=3, ge=1)
    lease_seconds: int = Field(default=60, ge=1)
