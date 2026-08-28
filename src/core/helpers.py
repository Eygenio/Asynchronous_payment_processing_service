import logging
from typing import Any

from src.rabbit.producer import publish_payment_to_dlq

logger = logging.getLogger(__name__)

async def publish_to_dlq(
    reason: str,
    payload: dict[str, Any],
    message_id: str | None = None,
) -> None:
    try:
        await publish_payment_to_dlq(
            {"reason": reason, "payload": payload},
            message_id=message_id,
        )
    except Exception:
        logger.exception("DLQ publish failed for message: %s", message_id)
        raise

def parse_retry_count(msg: Any, route: str) -> int:
    headers = getattr(msg, "headers", {}) or {}
    x_death = headers.get("x-death")
    if not isinstance(x_death, list):
        return 0

    queue_retry_count = 0
    for item in x_death:
        if not isinstance(item, dict):
            continue
        queue_name = item.get("queue")
        reason = item.get("reason")
        if queue_name != route or reason != "rejected":
            continue
        count = item.get("count", 0)
        if isinstance(count, int):
            queue_retry_count = max(queue_retry_count, count)
        elif isinstance(count, str) and count.isdigit():
            queue_retry_count = max(queue_retry_count, int(count))
    return queue_retry_count
