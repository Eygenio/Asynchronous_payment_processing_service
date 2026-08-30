from os import getenv
from uuid import uuid4

import pytest
from httpx import Client
from fastapi import status


pytestmark = pytest.mark.e2e


@pytest.fixture
def e2e_client() -> Client:
    base_url = getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
    api_key = getenv("API_KEY", "test-api-key")
    client = Client(
        base_url=base_url,
        headers={"X-API-Key": api_key},
        timeout=10.0,
    )
    try:
        yield client
    finally:
        client.close()


def test_health_check(e2e_client: Client) -> None:
    response = e2e_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}


def test_create_payment_and_get_payment(e2e_client: Client) -> None:
    payment_data = {
        "amount": "100.00",
        "currency": "USD",
        "description": "E2E payment",
        "metadata": {"source": "e2e"},
        "webhook_url": "https://example.com/webhook",
    }
    idempotency_key = str(uuid4())

    create_response = e2e_client.post(
        "/api/v1/payments",
        json=payment_data,
        headers={"Idempotency-Key": idempotency_key},
    )

    assert create_response.status_code == status.HTTP_202_ACCEPTED
    created = create_response.json()
    assert created["status"] == "pending"
    assert created["payment_id"]

    get_response = e2e_client.get(f"/api/v1/payments/{created['payment_id']}")
    assert get_response.status_code == status.HTTP_200_OK
    received = get_response.json()

    assert received["payment_id"] == created["payment_id"]
    assert received["amount"] == "100.00"
    assert received["currency"] == "USD"


def test_create_payment_requires_api_key() -> None:
    base_url = getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
    with Client(base_url=base_url, timeout=10.0) as client:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": "100.00",
                "currency": "USD",
                "description": "Unauthorized",
            },
            headers={"Idempotency-Key": str(uuid4())},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
