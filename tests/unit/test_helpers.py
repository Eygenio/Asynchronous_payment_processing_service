from collections import namedtuple

import pytest

from src.core.helpers import parse_retry_count

pytestmark = pytest.mark.unit

Message = namedtuple("Message", ["headers"])


def test_parse_retry_count_no_x_death() -> None:
    msg = Message(headers={})
    assert parse_retry_count(msg, "payments.new") == 0


def test_parse_retry_count_with_x_death_for_other_queue() -> None:
    msg = Message(headers={"x-death": [{"queue": "payments.other", "count": 5}]})
    assert parse_retry_count(msg, "payments.new") == 0


def test_parse_retry_count_extracts_max_count_for_target_queue() -> None:
    msg = Message(
        headers={
            "x-death": [
                {"queue": "payments.new", "count": 3},
                {"queue": "payments.new", "count": 7},
            ]
        }
    )
    assert parse_retry_count(msg, "payments.new") == 7


def test_parse_retry_count_handles_string_count() -> None:
    msg = Message(headers={"x-death": [{"queue": "payments.new", "count": "4"}]})
    assert parse_retry_count(msg, "payments.new") == 4
