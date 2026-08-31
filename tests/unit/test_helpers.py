from types import SimpleNamespace

import pytest

from src.core.helpers import parse_retry_count

pytestmark = pytest.mark.unit


def make_message(headers: dict) -> SimpleNamespace:
    return SimpleNamespace(headers=headers)


def test_parse_retry_count_no_x_death() -> None:
    msg = make_message({})

    assert parse_retry_count(msg, "payments.new") == 0


def test_parse_retry_count_with_x_death_for_other_queue() -> None:
    msg = make_message(
        {
            "x-death": [
                {
                    "queue": "payments.other",
                    "reason": "rejected",
                    "count": 5,
                }
            ]
        }
    )

    assert parse_retry_count(msg, "payments.new") == 0


def test_parse_retry_count_extracts_max_count_for_target_queue() -> None:
    msg = make_message(
        {
            "x-death": [
                {
                    "queue": "payments.new",
                    "reason": "rejected",
                    "count": 3,
                },
                {
                    "queue": "payments.new",
                    "reason": "rejected",
                    "count": 7,
                },
            ]
        }
    )

    assert parse_retry_count(msg, "payments.new") == 7


def test_parse_retry_count_handles_string_count() -> None:
    msg = make_message(
        {
            "x-death": [
                {
                    "queue": "payments.new",
                    "reason": "rejected",
                    "count": "4",
                }
            ]
        }
    )

    assert parse_retry_count(msg, "payments.new") == 4
