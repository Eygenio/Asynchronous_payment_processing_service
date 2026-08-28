import random
from datetime import UTC, datetime, timedelta

from src.config.settings import settings

BASE_RETRY_DELAY_SECONDS = settings.outbox_base_retry_delay_seconds
MAX_OUTBOX_ATTEMPTS = settings.outbox_max_attempts


def backoff_delay(attempts: int) -> datetime:
    current_time = datetime.now(UTC)
    exponential_delay = BASE_RETRY_DELAY_SECONDS * (2 ** max(attempts - 1, 0))
    delay_with_jitter = random.uniform(0, exponential_delay)
    return current_time + timedelta(seconds=delay_with_jitter)


def attempts_exhausted(
    attempts: int,
    max_attempts: int = MAX_OUTBOX_ATTEMPTS,
) -> bool:
    return attempts >= max_attempts
