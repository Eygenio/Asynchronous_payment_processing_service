import asyncio
import logging

from src.application.services.outbox import OutboxService
from src.core.constants import POLL_INTERVAL_SECONDS
from src.db.db import async_session_maker
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from src.rabbit.broker import broker, create_rabbit

logger = logging.getLogger(__name__)


async def run_outbox_dispatcher() -> None:
    async with broker:
        await create_rabbit()
        logger.info("Outbox dispatcher started")
        while True:
            try:
                async with async_session_maker() as session:
                    service = OutboxService(SQLAlchemyUnitOfWork(session))
                    stats = await service.dispatch_pending_outbox()

                if stats.selected:
                    logger.info(
                        "Outbox dispatch stats: selected=%s sent=%s failed=%s",
                        stats.selected,
                        stats.sent,
                        stats.failed,
                    )
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
            except Exception:
                logger.exception("Outbox dispatcher iteration failed")
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_outbox_dispatcher())
