import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config.settings import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.db.database_url,
    echo=settings.pool.echo,
    pool_pre_ping=settings.pool.pool_pre_ping,
    pool_size=settings.pool.pool_size,
    max_overflow=settings.pool.max_overflow,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
