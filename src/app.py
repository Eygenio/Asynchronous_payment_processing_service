import logging.config
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Depends

from src.config.logging_config import LOGGING_CONFIG
from src.config.settings import settings
from src.db.db import engine
from src.presentation.api.router import api_router
from src.presentation.dependencies import verify_api_key

logging.config.dictConfig(LOGGING_CONFIG)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_tables()
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.app.title,
    version=settings.app.version,
    description=settings.app.description,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("src.app:app", host=settings.app.host, port=settings.app.port, reload=True)
