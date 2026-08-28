from pydantic import BaseModel


class WebhookConfig(BaseModel):
    max_attempts: int
    base_delay_seconds: int
    timeout_seconds: int
