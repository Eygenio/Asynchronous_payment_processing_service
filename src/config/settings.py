import logging.config
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.app import AppConfig
from src.config.broker import BrokerConfig
from src.config.database import DatabaseConfig
from src.config.pool import DatabasePoolConfig
from src.config.logging_config import LOGGING_CONFIG

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig)
    broker: BrokerConfig = Field(default_factory=BrokerConfig)

    api_key: str = Field(default="test-api-key", alias="API_KEY")
    webhook_max_attempts: int = 3
    webhook_base_delay_seconds: int = 2
    webhook_timeout_seconds: int = 10
    outbox_base_retry_delay_seconds: int = 3
    outbox_max_attempts: int = 3
    max_consumer_retries: int = 3

    payments_exchange_name: str = "payments"
    payments_dlx_name: str = "payments.dlx"
    payment_new_route: str = "payments.new"
    payment_retry_route: str = "payments.new.retry"
    payment_dlq_route: str = "payments.new.dlq"
    payment_retry_delay_ms: int = 10000
    payments_new_topic: str = "payments.new"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.config.dictConfig(LOGGING_CONFIG)

settings = Settings()
