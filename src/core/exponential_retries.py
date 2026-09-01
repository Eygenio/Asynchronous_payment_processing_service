import random
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from src.config.settings import settings

BASE_RETRY_DELAY_SECONDS = settings.outbox.base_retry_delay_seconds
MAX_OUTBOX_ATTEMPTS = settings.outbox.max_attempts


def backoff_delay(
    attempts: int,
    base_delay_seconds: int = BASE_RETRY_DELAY_SECONDS,
    *,
    now: Callable[[], datetime] | None = None,
    jitter: Callable[[float, float], float] | None = None,
) -> datetime:
    current_time = (now or (lambda: datetime.now(UTC)))()
    exponential_delay = base_delay_seconds * (2 ** max(attempts - 1, 0))
    delay_with_jitter = (jitter or random.uniform)(0, exponential_delay)
    return current_time + timedelta(seconds=delay_with_jitter)


def attempts_exhausted(
    attempts: int,
    max_attempts: int = MAX_OUTBOX_ATTEMPTS,
) -> bool:
    return attempts >= max_attempts
