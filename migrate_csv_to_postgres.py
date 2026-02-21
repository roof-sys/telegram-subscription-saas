"""Скрипт миграции данных из CSV в PostgreSQL"""
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Добавляем путь к src в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database import init_db, get_db
from src.database.models import User, Payment, Subscription, Invite, PaymentStatus, PaymentMethod, SubscriptionStatus
from src.config import USERS_DB, PAYMENTS_DB, SUBSCRIPTIONS_DB, INVITES_DB


def parse_datetime(date_str: str) -> datetime:
    """Парсит дату из строки"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.utcnow()


def migrate_users():
    """Миграция пользователей"""
    if not os.path.exists(USERS_DB):
        print(f"⚠️  Файл {USERS_DB} не найден, пропускаем пользователей")
        return
    
    with get_db() as db:
        with open(USERS_DB, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    user = User(
                        user_id=int(row['user_id']),
                        username=row.get('username', ''),
                        registration_date=parse_datetime(row.get('registration_date', '')),
                        last_activity=parse_datetime(row.get('last_activity', ''))
                    )
                    db.add(user)
                    count += 1
                except Exception as e:
                    print(f"❌ Ошибка при миграции пользователя {row.get('user_id')}: {e}")
            
            print(f"✅ Мигрировано пользователей: {count}")


def migrate_payments():
    """Миграция платежей"""
    if not os.path.exists(PAYMENTS_DB):
        print(f"⚠️  Файл {PAYMENTS_DB} не найден, пропускаем платежи")
        return
    
    with get_db() as db:
        with open(PAYMENTS_DB, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    # Конвертируем метод оплаты
                    method_str = row.get('method', 'card').lower()
                    if 'usdt' in method_str:
                        method = PaymentMethod.USDT
                    elif 'сбп' in method_str or 'sbp' in method_str:
                        method = PaymentMethod.SBP
                    else:
                        method = PaymentMethod.CARD
                    
                    # Конвертируем статус
                    status_str = row.get('status', 'pending').lower()
                    if 'completed' in status_str or 'success' in status_str:
                        status = PaymentStatus.COMPLETED
                    elif 'failed' in status_str:
                        status = PaymentStatus.FAILED
                    elif 'cancelled' in status_str:
                        status = PaymentStatus.CANCELLED
                    else:
                        status = PaymentStatus.PENDING
                    
                    payment = Payment(
                        user_id=int(row['user_id']),
                        payment_id=row['payment_id'],
                        external_id=row.get('external_id', ''),
                        tariff=row.get('tariff', ''),
                        amount=float(row.get('amount', 0)),
                        status=status,
                        method=method,
                        payment_date=parse_datetime(row.get('payment_date', ''))
                    )
                    db.add(payment)
                    count += 1
                except Exception as e:
                    print(f"❌ Ошибка при миграции платежа {row.get('payment_id')}: {e}")
            
            print(f"✅ Мигрировано платежей: {count}")


def migrate_subscriptions():
    """Миграция подписок"""
    if not os.path.exists(SUBSCRIPTIONS_DB):
        print(f"⚠️  Файл {SUBSCRIPTIONS_DB} не найден, пропускаем подписки")
        return
    
    with get_db() as db:
        with open(SUBSCRIPTIONS_DB, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    status_str = row.get('status', 'active').lower()
                    if 'expired' in status_str:
                        status = SubscriptionStatus.EXPIRED
                    elif 'cancelled' in status_str:
                        status = SubscriptionStatus.CANCELLED
                    else:
                        status = SubscriptionStatus.ACTIVE
                    
                    subscription = Subscription(
                        user_id=int(row['user_id']),
                        payment_id=row.get('payment_id', ''),
                        tariff=row.get('tariff', ''),
                        start_date=parse_datetime(row.get('start_date', '')),
                        end_date=parse_datetime(row.get('end_date', '')),
                        status=status
                    )
                    db.add(subscription)
                    count += 1
                except Exception as e:
                    print(f"❌ Ошибка при миграции подписки для {row.get('user_id')}: {e}")
            
            print(f"✅ Мигрировано подписок: {count}")


def migrate_invites():
    """Миграция инвайтов"""
    if not os.path.exists(INVITES_DB):
        print(f"⚠️  Файл {INVITES_DB} не найден, пропускаем инвайты")
        return
    
    with get_db() as db:
        with open(INVITES_DB, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    is_used = row.get('is_used', 'False').lower() == 'true'
                    
                    invite = Invite(
                        user_id=int(row['user_id']),
                        chat_id=int(row['chat_id']),
                        invite_link=row['invite_link'],
                        is_used=is_used,
                        created_at=parse_datetime(row.get('created_at', ''))
                    )
                    db.add(invite)
                    count += 1
                except Exception as e:
                    print(f"❌ Ошибка при миграции инвайта: {e}")
            
            print(f"✅ Мигрировано инвайтов: {count}")


def main():
    """Главная функция миграции"""
    print("=" * 60)
    print("🔄 МИГРАЦИЯ ДАННЫХ ИЗ CSV В POSTGRESQL")
    print("=" * 60)
    
    print("\n📦 Инициализация базы данных...")
    init_db()
    
    print("\n👥 Миграция пользователей...")
    migrate_users()
    
    print("\n💳 Миграция платежей...")
    migrate_payments()
    
    print("\n📅 Миграция подписок...")
    migrate_subscriptions()
    
    print("\n🔗 Миграция инвайтов...")
    migrate_invites()
    
    print("\n" + "=" * 60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)
    print("\n💡 Что дальше:")
    print("1. Проверь данные в PostgreSQL")
    print("2. Сделай бэкап CSV файлов")
    print("3. Обнови src/database/db_manager.py (замени на новую версию)")
    print("4. Перезапусти бота")


if __name__ == '__main__':
    main()
