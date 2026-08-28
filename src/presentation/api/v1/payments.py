from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.domain.entities import Payment
from src.application.services.payments import PaymentService
from src.presentation.dependencies import PaymentServiceDep
from src.presentation.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment(
    payment_id: UUID,
    service: PaymentServiceDep,
) -> Payment:
    payment = await service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@router.post(
    "/",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment(
    payload: PaymentCreateRequest,
    service: PaymentServiceDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=255)],
) -> Payment:
    try:
        payment = await service.create_payment(payload, idempotency_key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return payment
