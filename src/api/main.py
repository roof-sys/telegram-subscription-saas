"""FastAPI приложение для REST API"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import stats, users, payments, webhook

# Создаём FastAPI приложение
app = FastAPI(
    title="Telegram Bot API",
    description="REST API для управления и аналитики Telegram-бота",
    version="1.0.0"
)

# CORS middleware (разрешает запросы с других доменов)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажи конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(payments.router, prefix="/api", tags=["Payments"])
app.include_router(webhook.router, prefix="/api", tags=["Webhooks"])


@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Telegram Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "OK"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "healthy"}