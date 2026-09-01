from pydantic import BaseModel
from sqlalchemy import URL


class DatabaseConfig(BaseModel):
    name: str = "payments"
    user: str = "postgres"
    password: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    driver_name: str = "postgresql+asyncpg"

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername=self.driver_name,
            database=self.name,
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
        )
