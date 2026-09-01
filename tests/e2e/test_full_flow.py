import pytest
from fastapi import status
from httpx import Client

pytestmark = pytest.mark.e2e


def test_payment_idempotency_flow(
    e2e_client: Client,
    payment_payload: dict,
    authorized_headers: dict[str, str],
) -> None:
    first = e2e_client.post(
        "/api/v1/payments",
        json=payment_payload,
        headers=authorized_headers,
    )
    assert first.status_code == status.HTTP_202_ACCEPTED

    second = e2e_client.post(
        "/api/v1/payments",
        json=payment_payload,
        headers=authorized_headers,
    )
    assert second.status_code == status.HTTP_202_ACCEPTED
    assert second.json()["payment_id"] == first.json()["payment_id"]

    payment_id = first.json()["payment_id"]
    response = e2e_client.get(
        f"/api/v1/payments/{payment_id}",
        headers=authorized_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["payment_id"] == payment_id
