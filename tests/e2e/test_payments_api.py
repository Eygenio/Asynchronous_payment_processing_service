from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4, UUID

from fastapi import status
from fastapi.testclient import TestClient

from src.application.dto.payments import PaymentCreateDTO
from src.application.services.payments import PaymentService
from src.core.enums import Currency, PaymentStatus
from src.domain.entities import Payment


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


async def test_create_payment_returns_existing_payment(
    service: PaymentService,
    mock_uow,
) -> None:
    existing_payment = Payment(
        payment_id=UUID(
            "12345678-1234-5678-1234-567812345678"
        ),
        amount=Decimal("100.00"),
        currency=Currency.USD,
        description="test",
        metadata_={},
        status=PaymentStatus.PENDING,
        idempotency_key="key1",
        webhook_url=None,
        created_at=datetime(2025, 1, 1),
    )

    mock_uow.payments.get_by_idempotency_key.return_value = (
        existing_payment
    )

    data = PaymentCreateDTO(
        amount=Decimal("100.00"),
        currency=Currency.USD,
        description="test",
        metadata={},
        webhook_url=None,
    )

    result = await service.create_payment(
        data,
        "key1",
    )

    assert result is existing_payment
    mock_uow.commit.assert_not_awaited()
    mock_uow.outbox.add.assert_not_awaited()
