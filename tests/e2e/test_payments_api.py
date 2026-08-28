from fastapi import status
from fastapi.testclient import TestClient

def test_health_check(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

def test_create_payment_missing_api_key(api_client: TestClient, sample_payment_data: dict) -> None:
    response = api_client.post("/api/v1/payments", json=sample_payment_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_payment_invalid_api_key(api_client: TestClient, sample_payment_data: dict) -> None:
    response = api_client.post(
        "/api/v1/payments",
        json=sample_payment_data,
        headers={"X-API-Key": "wrong", "Idempotency-Key": "test-key"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_create_payment_success(api_client: TestClient, sample_payment_data: dict) -> None:
    headers = {"X-API-Key": "test-api-key", "Idempotency-Key": "unique-key-1"}
    response = api_client.post("/api/v1/payments", json=sample_payment_data, headers=headers)
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "payment_id" in data
    assert data["status"] == "pending"
