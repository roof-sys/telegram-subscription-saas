"""Обработчик для проверки подписки"""
from aiogram import types
from aiogram.filters import Command
from datetime import datetime

from src.database.db_manager import get_active_subscription
from src.bot import dp


@dp.message(Command("mysub"))
async def check_my_subscription(message: types.Message):
    """Показывает информацию о текущей подписке"""
    user_id = message.from_user.id
    subscription = get_active_subscription(user_id)

    if subscription:
        # Определяем, сколько дней осталось
        if "Навсегда" in subscription['tariff'] or subscription['tariff'] == 'all':
            days_left = "∞ (Навсегда)"
        else:
            end_date = datetime.strptime(subscription['end_date'], "%Y-%m-%d %H:%M:%S")
            days_left = (end_date - datetime.now()).days
            days_left = f"{max(days_left, 0)} дней"

        await message.answer(
            f"✅ <b>Ваша подписка активна</b>\n\n"
            f"📌 Тариф: {subscription['tariff']}\n"
            f"📅 Дата окончания: {subscription['end_date'] if 'Навсегда' not in subscription['tariff'] else 'Навсегда'}\n"
            f"⏳ Осталось: {days_left}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>У вас нет активной подписки</b>\n\n"
            "Чтобы получить доступ, выберите тариф в меню бота.",
            parse_mode="HTML"
        )