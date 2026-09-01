import logging.config

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.app import AppConfig
from src.config.broker import BrokerConfig
from src.config.database import DatabaseConfig
from src.config.logging_config import LOGGING_CONFIG
from src.config.outbox import OutboxConfig
from src.config.payment import PaymentConfig
from src.config.pool import DatabasePoolConfig
from src.config.webhook import WebhookConfig


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
    payment: PaymentConfig = Field(default_factory=PaymentConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    outbox: OutboxConfig = Field(default_factory=OutboxConfig)

    api_key: str = Field(default="test-api-key", alias="API_KEY")
    test_db_name: str = Field(default="test_payments", alias="TEST_DB_NAME")
    test_base_url: str = Field(default="http://127.0.0.1:8000", alias="TEST_BASE_URL")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.config.dictConfig(LOGGING_CONFIG)


settings = Settings()
