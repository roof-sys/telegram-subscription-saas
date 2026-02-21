"""Подключение к базе данных и управление сессиями"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

from .models import Base

logger = logging.getLogger(__name__)

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/telegram_bot'
)

# Создаём движок базы данных
# pool_pre_ping=True - проверяет соединение перед использованием
# echo=False - не логирует SQL запросы (можно включить для отладки)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    pool_size=10,
    max_overflow=20
)

# Создаём фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Thread-safe scoped session для использования в async коде
ScopedSession = scoped_session(SessionLocal)


def init_db():
    """
    Инициализирует базу данных.
    Создаёт все таблицы, если их нет.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}", exc_info=True)
        raise


def drop_all_tables():
    """
    ВНИМАНИЕ: Удаляет все таблицы!
    Использовать только в разработке!
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠️ Все таблицы удалены")


@contextmanager
def get_db():
    """
    Context manager для работы с сессией БД.

    Использование:
        with get_db() as db:
            user = db.query(User).first()

    Автоматически закрывает сессию и откатывает транзакцию при ошибке.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка в транзакции БД: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_session():
    """
    Возвращает новую сессию БД.
    Используется когда нужен полный контроль над сессией.

    ВАЖНО: Не забывай закрывать сессию вручную!

    Использование:
        db = get_session()
        try:
            # работа с БД
            db.commit()
        finally:
            db.close()
    """
    return SessionLocal()
