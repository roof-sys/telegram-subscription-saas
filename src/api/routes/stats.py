"""Эндпоинт для статистики"""
from fastapi import APIRouter
from sqlalchemy import func

from src.database.database import get_db
from src.database.models import User, Payment, Subscription, PaymentStatus, SubscriptionStatus

router = APIRouter()


@router.get("/stats")
async def get_statistics():
    """
    Получить общую статистику

    Возвращает:
    - Общее количество пользователей
    - Количество платежей (всего и успешных)
    - Количество активных подписок
    - Общую сумму платежей
    """
    with get_db() as db:
        # Общее количество пользователей
        total_users = db.query(func.count(User.id)).scalar()

        # Количество платежей
        total_payments = db.query(func.count(Payment.id)).scalar()
        completed_payments = db.query(func.count(Payment.id)).filter(
            Payment.status == PaymentStatus.COMPLETED
        ).scalar()

        # Общая сумма успешных платежей
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.COMPLETED
        ).scalar() or 0

        # Активные подписки
        active_subscriptions = db.query(func.count(Subscription.id)).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).scalar()

        return {
            "users": {
                "total": total_users
            },
            "payments": {
                "total": total_payments,
                "completed": completed_payments,
                "pending": total_payments - completed_payments
            },
            "revenue": {
                "total": float(total_revenue),
                "currency": "RUB"
            },
            "subscriptions": {
                "active": active_subscriptions
            }
        }