"""Обработчик команды /start и главное меню"""
from aiogram import types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from src.database.db_manager import save_user
from src.config import TARIFFS
from src.bot import dp


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Главное меню с тарифами"""
    user = message.from_user
    save_user(user.id, user.username)

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для всех тарифов
    for tariff_id, tariff in TARIFFS.items():
        builder.add(InlineKeyboardButton(
            text=tariff['name'],
            callback_data=f"tariff:{tariff_id}"
        ))

    # По одной кнопке в ряд
    builder.adjust(1)

    await message.answer(
        "👋 Добро пожаловать! Выберите тариф:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await start_command(callback.message)
    await callback.answer()