from pydantic import BaseModel


class BrokerConfig(BaseModel):
    url: str
    result_backend: str
