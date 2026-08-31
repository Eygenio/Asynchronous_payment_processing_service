import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from httpx import Client

from tests.factories import PaymentPayloadFactory


@pytest.fixture
def e2e_client() -> Iterator[Client]:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
    with Client(base_url=base_url, timeout=10.0) as client:
        yield client


@pytest.fixture
def payment_payload() -> dict:
    return PaymentPayloadFactory.build()


@pytest.fixture
def idempotency_key() -> str:
    return str(uuid4())


@pytest.fixture
def authorized_headers(idempotency_key: str) -> dict[str, str]:
    api_key = os.getenv("API_KEY", "test-api-key")
    return {"X-API-Key": api_key, "Idempotency-Key": idempotency_key}


@pytest.fixture
def invalid_api_key_headers(idempotency_key: str) -> dict[str, str]:
    return {"X-API-Key": "wrong", "Idempotency-Key": idempotency_key}
