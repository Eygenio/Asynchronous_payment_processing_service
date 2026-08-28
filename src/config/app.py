from pydantic import BaseModel


class AppConfig(BaseModel):
    title: str = "Payment Processing Service"
    version: str = "0.1.0"
    description: str = "API for async payment processing"
    host: str
    port: int
