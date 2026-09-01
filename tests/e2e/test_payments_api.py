import pytest
from fastapi import status
from httpx import Client

pytestmark = pytest.mark.e2e


def test_health_check(e2e_client: Client) -> None:
    response = e2e_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}


def test_create_payment_missing_api_key(
    e2e_client: Client,
    payment_payload: dict,
    idempotency_key: str,
) -> None:
    response = e2e_client.post(
        "/api/v1/payments",
        json=payment_payload,
        headers={"Idempotency-Key": idempotency_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_payment_invalid_api_key(
    e2e_client: Client,
    payment_payload: dict,
    invalid_api_key_headers: dict[str, str],
) -> None:
    response = e2e_client.post(
        "/api/v1/payments",
        json=payment_payload,
        headers=invalid_api_key_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_payment_and_get_payment(
    e2e_client: Client,
    payment_payload: dict,
    authorized_headers: dict[str, str],
) -> None:
    response = e2e_client.post(
        "/api/v1/payments",
        json=payment_payload,
        headers=authorized_headers,
    )
    assert response.status_code == status.HTTP_202_ACCEPTED

    payment_id = response.json()["payment_id"]
    get_response = e2e_client.get(
        f"/api/v1/payments/{payment_id}",
        headers=authorized_headers,
    )

    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["payment_id"] == payment_id
