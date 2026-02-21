"""Точка входа в приложение"""
import asyncio
import logging

from src.bot import bot, dp
from src.database.database import init_db
from src.utils.logger import setup_logger
from src.services.scheduler import check_subscriptions
from src import handlers   # Импортируем все обработчики


async def main():
    """Запуск бота"""
    # Настройка логирования
    setup_logger()

    # Инициализация базы данных
    init_db()
    logging.info("База данных инициализирована")

    # Запуск фоновой задачи проверки подписок
    asyncio.create_task(check_subscriptions())

    logging.info("🚀 Бот запущен и готов к работе")

    try:
        # Запускаем поллинг
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logging.info("Бот остановлен")


if __name__ == '__main__':
    asyncio.run(main())