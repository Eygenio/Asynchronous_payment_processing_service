from pydantic import BaseModel


class BrokerConfig(BaseModel):
    url: str = "amqp://guest:guest@localhost:5672/"
    result_backend: str = "rpc://"
