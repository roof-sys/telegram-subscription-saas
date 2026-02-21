"""Эндпоинт для работы с пользователями"""
from fastapi import APIRouter, Query
from typing import Optional

from src.database.database import get_db
from src.database.models import User

router = APIRouter()


@router.get("/users")
async def get_users(
        limit: int = Query(default=50, ge=1, le=100, description="Количество пользователей"),
        offset: int = Query(default=0, ge=0, description="Смещение для пагинации")
):
    """
    Получить список пользователей

    Параметры:
    - limit: количество пользователей (от 1 до 100)
    - offset: смещение для пагинации
    """
    with get_db() as db:
        users = db.query(User).offset(offset).limit(limit).all()

        return {
            "total": db.query(User).count(),
            "limit": limit,
            "offset": offset,
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "registration_date": user.registration_date.isoformat(),
                    "last_activity": user.last_activity.isoformat()
                }
                for user in users
            ]
        }


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    Получить информацию о конкретном пользователе

    Параметры:
    - user_id: Telegram ID пользователя
    """
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            return {"error": "User not found"}, 404

        # Считаем статистику пользователя
        payments_count = len(user.payments)
        subscriptions_count = len(user.subscriptions)

        return {
            "user_id": user.user_id,
            "username": user.username,
            "registration_date": user.registration_date.isoformat(),
            "last_activity": user.last_activity.isoformat(),
            "stats": {
                "payments": payments_count,
                "subscriptions": subscriptions_count
            }
        }