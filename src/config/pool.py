from pydantic import BaseModel


class DatabasePoolConfig(BaseModel):
    echo: bool
    pool_pre_ping: bool
    pool_size: int
    max_overflow: int
