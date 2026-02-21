"""Менеджер базы данных на PostgreSQL + SQLAlchemy"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from .database import get_db
from .models import (
    User, Payment, Subscription, Invite,
    PaymentStatus, PaymentMethod, SubscriptionStatus
)

logger = logging.getLogger(__name__)


# ПОЛЬЗОВАТЕЛИ

def save_user(user_id: int, username: str = None) -> User:
    """
    Сохраняет или обновляет пользователя в базе.

    Args:
        user_id: Telegram user ID
        username: Telegram username

    Returns:
        User: Объект пользователя
    """
    with get_db() as db:
        # Ищем существующего пользователя
        user = db.query(User).filter(User.user_id == user_id).first()

        if user:
            # Обновляем существующего
            if username:
                user.username = username
            user.last_activity = datetime.utcnow()
            logger.debug(f"Пользователь {user_id} обновлён")
        else:
            # Создаём нового
            user = User(
                user_id=user_id,
                username=username or ''
            )
            db.add(user)
            logger.info(f"Создан новый пользователь {user_id}")

        db.flush()
        db.refresh(user)
        return user


def get_user(user_id: int) -> Optional[User]:
    """Возвращает пользователя по Telegram ID"""
    with get_db() as db:
        return db.query(User).filter(User.user_id == user_id).first()


# ПЛАТЕЖИ

def save_payment(
        user_id: int,
        username: str,
        tariff: str,
        amount: float,
        payment_id: str,
        status: str = "pending",
        method: str = "card",
        external_id: str = None
) -> Payment:
    """
    Сохраняет новый платёж.

    Args:
        user_id: Telegram user ID
        username: Telegram username
        tariff: Название тарифа
        amount: Сумма платежа
        payment_id: Внутренний ID платежа
        status: Статус платежа (pending/completed/failed)
        method: Метод оплаты (card/sbp/usdt)
        external_id: ID от платёжной системы

    Returns:
        Payment: Объект платежа
    """
    with get_db() as db:
        # Убеждаемся что пользователь существует
        save_user(user_id, username)

        # Конвертируем строковые значения в enum
        payment_status = PaymentStatus(status.lower())
        payment_method = PaymentMethod(method.lower())

        payment = Payment(
            user_id=user_id,
            payment_id=payment_id,
            external_id=external_id,
            tariff=tariff,
            amount=amount,
            status=payment_status,
            method=payment_method
        )

        db.add(payment)
        db.flush()
        db.refresh(payment)

        logger.info(f"Платёж {payment_id} создан (статус: {status}, метод: {method})")
        return payment


def update_payment_status(payment_id: str, status: str, external_id: str = None) -> bool:
    """
    Обновляет статус платежа.

    Args:
        payment_id: ID платежа
        status: Новый статус
        external_id: Внешний ID (опционально)

    Returns:
        bool: True если обновлено успешно
    """
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

        if not payment:
            logger.warning(f"Платёж {payment_id} не найден")
            return False

        payment.status = PaymentStatus(status.lower())
        if external_id:
            payment.external_id = external_id

        logger.info(f"Статус платежа {payment_id} обновлён на {status}")
        return True


def get_payment(payment_id: str) -> Optional[Dict]:
    """
    Возвращает информацию о платеже.

    Returns:
        Dict с данными платежа или None
    """
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

        if not payment:
            return None

        return {
            'user_id': payment.user_id,
            'username': payment.user.username,
            'tariff': payment.tariff,
            'amount': payment.amount,
            'payment_id': payment.payment_id,
            'status': payment.status.value,
            'method': payment.method.value,
            'payment_date': payment.payment_date.strftime("%Y-%m-%d %H:%M:%S"),
            'external_id': payment.external_id or ''
        }


# ПОДПИСКИ

def save_subscription(user_id: int, username: str, tariff: str, payment_id: str) -> Subscription:
    """
    Создаёт новую подписку.

    Args:
        user_id: Telegram user ID
        username: Telegram username
        tariff: Название тарифа
        payment_id: ID связанного платежа

    Returns:
        Subscription: Объект подписки
    """
    with get_db() as db:
        # Убеждаемся что пользователь существует
        save_user(user_id, username)

        start_date = datetime.utcnow()

        # Определяем дату окончания
        if "Навсегда" in tariff or tariff == "all":
            end_date = datetime(2100, 1, 1)  # "Вечная" подписка
        else:
            end_date = start_date + timedelta(days=30)

        subscription = Subscription(
            user_id=user_id,
            payment_id=payment_id,
            tariff=tariff,
            start_date=start_date,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE
        )

        db.add(subscription)
        db.flush()
        db.refresh(subscription)

        logger.info(f"Подписка для пользователя {user_id} создана (тариф: {tariff})")
        return subscription


def update_subscription_status(payment_id: str, status: str) -> bool:
    """Обновляет статус подписки по ID платежа"""
    with get_db() as db:
        subscription = db.query(Subscription).filter(
            Subscription.payment_id == payment_id
        ).first()

        if not subscription:
            logger.warning(f"Подписка с payment_id={payment_id} не найдена")
            return False

        subscription.status = SubscriptionStatus(status.lower())
        logger.info(f"Статус подписки {payment_id} обновлён на {status}")
        return True


def get_active_subscription(user_id: int) -> Optional[Dict]:
    """
    Возвращает активную подписку пользователя.

    Returns:
        Dict с данными подписки или None
    """
    with get_db() as db:
        now = datetime.utcnow()

        subscription = db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date > now
            )
        ).first()

        if not subscription:
            return None

        return {
            'user_id': subscription.user_id,
            'username': subscription.user.username,
            'tariff': subscription.tariff,
            'start_date': subscription.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            'end_date': subscription.end_date.strftime("%Y-%m-%d %H:%M:%S"),
            'status': subscription.status.value,
            'payment_id': subscription.payment_id
        }


def get_all_active_subscriptions() -> List[Dict]:
    """Возвращает список всех активных подписок"""
    with get_db() as db:
        now = datetime.utcnow()

        subscriptions = db.query(Subscription).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date > now
            )
        ).all()

        return [
            {
                'user_id': sub.user_id,
                'username': sub.user.username,
                'tariff': sub.tariff,
                'start_date': sub.start_date.strftime("%Y-%m-%d %H:%M:%S"),
                'end_date': sub.end_date.strftime("%Y-%m-%d %H:%M:%S"),
                'status': sub.status.value,
                'payment_id': sub.payment_id
            }
            for sub in subscriptions
        ]


def expire_subscription(user_id: int, tariff: str) -> bool:
    """Помечает подписку как истёкшую"""
    with get_db() as db:
        subscription = db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.tariff == tariff,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()

        if not subscription:
            return False

        subscription.status = SubscriptionStatus.EXPIRED
        logger.info(f"Подписка пользователя {user_id} на {tariff} истекла")
        return True


# ИНВАЙТЫ

def save_invite(user_id: int, chat_id: int, invite_link: str) -> Invite:
    """Сохраняет новую инвайт-ссылку"""
    with get_db() as db:
        invite = Invite(
            user_id=user_id,
            chat_id=chat_id,
            invite_link=invite_link
        )

        db.add(invite)
        db.flush()
        db.refresh(invite)

        logger.debug(f"Инвайт для {user_id} в чат {chat_id} сохранён")
        return invite


def mark_invite_used(invite_link: str) -> bool:
    """Помечает инвайт-ссылку как использованную"""
    with get_db() as db:
        invite = db.query(Invite).filter(Invite.invite_link == invite_link).first()

        if not invite:
            logger.warning(f"Инвайт {invite_link} не найден")
            return False

        invite.mark_as_used()
        logger.debug(f"Инвайт {invite_link} помечен как использованный")
        return True


def is_valid_invite(user_id: int, chat_id: int, invite_link: str) -> bool:
    """Проверяет, действительна ли инвайт-ссылка"""
    with get_db() as db:
        invite = db.query(Invite).filter(
            and_(
                Invite.user_id == user_id,
                Invite.chat_id == chat_id,
                Invite.invite_link == invite_link,
                Invite.is_used == False
            )
        ).first()

        return invite is not None