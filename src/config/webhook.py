from pydantic import BaseModel, Field


class WebhookConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1)
    base_delay_seconds: int = Field(default=2, ge=1)
    timeout_seconds: int = Field(default=10, ge=1)
    allow_private_networks: bool = False
