import pytest
from datetime import UTC, datetime, timedelta

from src.core.exponential_retries import attempts_exhausted, backoff_delay


@pytest.fixture
def fixed_datetime():
    fixed = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return fixed

    return FakeDatetime


def test_backoff_delay_first_attempt_is_within_range(monkeypatch, fixed_datetime):
    monkeypatch.setattr(
        "src.core.exponential_retries.random.uniform",
        lambda a, b: 0.0,
    )
    monkeypatch.setattr(
        "src.core.exponential_retries.datetime",
        fixed_datetime,
    )
    result = backoff_delay(attempts=1, base_delay_seconds=3)
    assert result == datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)


def test_backoff_delay_increases_exponentially(monkeypatch, fixed_datetime):
    monkeypatch.setattr(
        "src.core.exponential_retries.random.uniform",
        lambda a, b: b,
    )
    monkeypatch.setattr(
        "src.core.exponential_retries.datetime",
        fixed_datetime,
    )
    first = backoff_delay(attempts=1, base_delay_seconds=3)
    second = backoff_delay(attempts=2, base_delay_seconds=3)
    third = backoff_delay(attempts=3, base_delay_seconds=3)

    fixed = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    assert first == fixed + timedelta(seconds=3)
    assert second == fixed + timedelta(seconds=6)
    assert third == fixed + timedelta(seconds=12)


def test_attempts_exhausted():
    assert attempts_exhausted(3, max_attempts=3) is True
    assert attempts_exhausted(2, max_attempts=3) is False
    assert attempts_exhausted(4, max_attempts=3) is True
