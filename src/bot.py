"""Инициализация бота и диспетчера"""
from aiogram import Bot, Dispatcher
from src.config import BOT_TOKEN

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()