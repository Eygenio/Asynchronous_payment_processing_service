from pydantic import BaseModel
from sqlalchemy import URL


class DatabaseConfig(BaseModel):
    name: str
    user: str
    password: str
    host: str
    port: int
    driver_name: str

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
