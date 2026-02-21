"""Эндпоинт для работы с платежами"""
from fastapi import APIRouter, Query
from typing import Optional

from src.database.database import get_db
from src.database.models import Payment, PaymentStatus

router = APIRouter()


@router.get("/payments")
async def get_payments(
        status: Optional[str] = Query(default=None, description="Фильтр по статусу (pending/completed/failed)"),
        limit: int = Query(default=50, ge=1, le=100, description="Количество платежей"),
        offset: int = Query(default=0, ge=0, description="Смещение для пагинации")
):
    """
    Получить список платежей

    Параметры:
    - status: фильтр по статусу (pending, completed, failed, cancelled)
    - limit: количество платежей (от 1 до 100)
    - offset: смещение для пагинации
    """
    with get_db() as db:
        query = db.query(Payment)

        # Фильтр по статусу если указан
        if status:
            try:
                payment_status = PaymentStatus(status.lower())
                query = query.filter(Payment.status == payment_status)
            except ValueError:
                return {"error": f"Invalid status: {status}"}, 400

        # Сортировка по дате (новые первые)
        query = query.order_by(Payment.payment_date.desc())

        total = query.count()
        payments = query.offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "payments": [
                {
                    "payment_id": payment.payment_id,
                    "user_id": payment.user_id,
                    "tariff": payment.tariff,
                    "amount": payment.amount,
                    "status": payment.status.value,
                    "method": payment.method.value,
                    "payment_date": payment.payment_date.isoformat(),
                    "external_id": payment.external_id
                }
                for payment in payments
            ]
        }


@router.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    """
    Получить информацию о конкретном платеже

    Параметры:
    - payment_id: ID платежа
    """
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

        if not payment:
            return {"error": "Payment not found"}, 404

        return {
            "payment_id": payment.payment_id,
            "user_id": payment.user_id,
            "username": payment.user.username if payment.user else None,
            "tariff": payment.tariff,
            "amount": payment.amount,
            "status": payment.status.value,
            "method": payment.method.value,
            "payment_date": payment.payment_date.isoformat(),
            "updated_at": payment.updated_at.isoformat(),
            "external_id": payment.external_id
        }