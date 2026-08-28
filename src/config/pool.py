from pydantic import BaseModel, Field


class DatabasePoolConfig(BaseModel):
    echo: bool = False
    pool_pre_ping: bool = True
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)
