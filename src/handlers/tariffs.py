"""Обработчики для показа тарифов"""
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

from src.config import TARIFFS
from src.bot import dp


@dp.callback_query(lambda c: c.data.startswith("tariff:"))
async def show_tariff(callback: types.CallbackQuery):
    """Показывает детали выбранного тарифа"""
    tariff_id = callback.data.split(':')[1]
    tariff = TARIFFS.get(tariff_id)

    if not tariff:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return

    # Особый случай - тариф "all" (все каналы)
    if tariff_id == 'all':
        keyboard = [
            [InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay:{tariff_id}:forever")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
        ]

        await callback.message.edit_text(
            f"📌 <b>{tariff['name']}</b>\n\n"
            f"💵 Сумма: <b>{tariff['forever']}₽</b>\n"
            f"⏳ Срок: <b>Навсегда</b>\n\n"
            f"📝 Описание:\n{tariff['description']}\n\n"
            "Выберите действие:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        # Обычные тарифы
        keyboard = []

        if tariff['30_days']:
            keyboard.append([InlineKeyboardButton(
                text=f"💳 {tariff['30_days']}₽ (30 дней)",
                callback_data=f"pay:{tariff_id}:30_days"
            )])
        if tariff['forever']:
            keyboard.append([InlineKeyboardButton(
                text=f"💳 {tariff['forever']}₽ (Навсегда)",
                callback_data=f"pay:{tariff_id}:forever"
            )])

        keyboard.append([InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_start"
        )])

        await callback.message.edit_text(
            f"📌 <b>{tariff['name']}</b>\n\n"
            f"📝 Описание:\n{tariff['description']}\n\n"
            f"Выберите срок подписки:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    await callback.answer()