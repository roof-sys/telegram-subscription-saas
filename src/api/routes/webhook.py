"""Эндпоинт для webhook уведомлений от платёжных систем"""
from fastapi import APIRouter, Request, HTTPException
import hashlib
import logging

from src.database.db_manager import update_payment_status, save_subscription
from src.config import SHOP_SECRET

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook/payment")
async def payment_webhook(request: Request):
    """
    Webhook для получения уведомлений от платёжной системы

    Обрабатывает callback о статусе платежа и активирует подписку
    """
    try:
        # Получаем данные
        data = await request.json()

        # Извлекаем необходимые поля
        payment_id = data.get('merchant_order_id')
        external_id = data.get('payment_id') or data.get('id')
        status = data.get('status')
        sign = data.get('sign')

        if not all([payment_id, external_id, status]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Проверка подписи (если требуется вашей платёжной системой)
        # expected_sign = hashlib.md5(f"{payment_id}:{external_id}:{SHOP_SECRET}".encode()).hexdigest()
        # if sign != expected_sign:
        #     raise HTTPException(status_code=403, detail="Invalid signature")

        # Обновляем статус платежа
        if status == 1 or status == 'success' or status == 'completed':
            # Платёж успешен
            update_payment_status(payment_id, 'completed', external_id)

            # Здесь можно активировать подписку
            # (требует доработки для получения данных пользователя и тарифа)

            logger.info(f"Webhook: платёж {payment_id} успешно обработан")

            return {"status": "ok", "message": "Payment processed"}

        elif status in [2, 'failed', 'error']:
            # Платёж отклонён
            update_payment_status(payment_id, 'failed', external_id)
            logger.warning(f"Webhook: платёж {payment_id} отклонён")

            return {"status": "ok", "message": "Payment failed"}

        else:
            # Неизвестный статус
            logger.warning(f"Webhook: неизвестный статус {status} для платежа {payment_id}")
            return {"status": "ok", "message": "Unknown status"}

    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook/test")
async def test_webhook():
    """Тестовый эндпоинт для проверки работы webhook"""
    return {
        "status": "ok",
        "message": "Webhook endpoint is working",
        "endpoint": "/api/webhook/payment"
    }