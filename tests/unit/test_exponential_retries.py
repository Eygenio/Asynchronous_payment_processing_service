from datetime import UTC, datetime, timedelta

import pytest

from src.core.exponential_retries import attempts_exhausted, backoff_delay

pytestmark = pytest.mark.unit


def test_backoff_delay_uses_injected_clock_and_jitter() -> None:
    fixed = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)

    result = backoff_delay(
        attempts=1,
        base_delay_seconds=3,
        now=lambda: fixed,
        jitter=lambda _min, _max: 0.0,
    )

    assert result == fixed


def test_backoff_delay_increases_exponentially() -> None:
    fixed = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)

    def jitter(_min: float, maximum: float) -> float:
        return maximum

    first = backoff_delay(1, 3, now=lambda: fixed, jitter=jitter)
    second = backoff_delay(2, 3, now=lambda: fixed, jitter=jitter)
    third = backoff_delay(3, 3, now=lambda: fixed, jitter=jitter)

    assert first == fixed + timedelta(seconds=3)
    assert second == fixed + timedelta(seconds=6)
    assert third == fixed + timedelta(seconds=12)


def test_attempts_exhausted() -> None:
    assert attempts_exhausted(3, max_attempts=3) is True
    assert attempts_exhausted(2, max_attempts=3) is False
    assert attempts_exhausted(4, max_attempts=3) is True
