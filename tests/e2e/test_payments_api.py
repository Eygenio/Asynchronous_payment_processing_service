from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}


def test_create_payment_missing_api_key(
    api_client: TestClient,
    sample_payment_data: dict,
) -> None:
    response = api_client.post("/api/v1/payments", json=sample_payment_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_payment_invalid_api_key(
    api_client: TestClient,
    sample_payment_data: dict,
) -> None:
    response = api_client.post(
        "/api/v1/payments",
        json=sample_payment_data,
        headers={"X-API-Key": "wrong", "Idempotency-Key": "test-key"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_payment_success(
    api_client: TestClient,
    sample_payment_data: dict,
    mock_uow: MagicMock,
) -> None:
    async def add_side_effect(payment: MagicMock) -> None:
        payment.payment_id = uuid4()
        payment.created_at = datetime.now(UTC)
        return payment

    mock_uow.payments.add.side_effect = add_side_effect
    mock_uow.payments.get_by_idempotency_key.return_value = None
    mock_uow.outbox.add.side_effect = None
    mock_uow.payments.refresh.side_effect = None

    headers = {
        "X-API-Key": "test-api-key",
        "Idempotency-Key": str(uuid4()),
    }
    response = api_client.post("/api/v1/payments", json=sample_payment_data, headers=headers)
    assert response.status_code == status.HTTP_202_ACCEPTED
