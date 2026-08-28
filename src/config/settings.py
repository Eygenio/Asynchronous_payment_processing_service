import logging.config
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.app import AppConfig
from src.config.broker import BrokerConfig
from src.config.database import DatabaseConfig
from src.config.pool import DatabasePoolConfig
from src.config.payment import PaymentConfig
from src.config.webhook import WebhookConfig
from src.config.outbox import OutboxConfig
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
    payment: PaymentConfig = Field(default_factory=PaymentConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    outbox: OutboxConfig = Field(default_factory=OutboxConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.config.dictConfig(LOGGING_CONFIG)

settings = Settings()
