"""Фоновые задачи"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_subscriptions():
    """
    Фоновая задача для проверки истекших подписок.
    Запускается каждый час.
    """
    while True:
        try:
            logger.info("🔄 Проверка истекших подписок...")

            # Здесь будет логика проверки подписок
            # Пока просто заглушка

            logger.info("✅ Проверка подписок завершена")

        except Exception as e:
            logger.error(f"Ошибка в check_subscriptions: {e}", exc_info=True)

        # Ждем 1 час до следующей проверки
        await asyncio.sleep(3600)