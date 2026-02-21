
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# ТОКЕНЫ И КЛЮЧИ
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# ПЛАТЕЖИ (карты/СБП)
SHOP_ID = int(os.getenv('SHOP_ID', 0))
SHOP_SECRET = os.getenv('SHOP_SECRET')
ACQUIRING_API_URL = os.getenv('ACQUIRING_API_URL')

# КРИПТОВАЛЮТА (USDT)
CRYPTO_PAYMENT_ADDRESS = os.getenv('CRYPTO_PAYMENT_ADDRESS')
CRYPTO_PAYMENT_NETWORK = os.getenv('CRYPTO_PAYMENT_NETWORK', 'TRC-20')
CRYPTO_EXCHANGE_RATE = float(os.getenv('CRYPTO_EXCHANGE_RATE', 90))  # Курс USDT к RUB
TRONGRID_API_KEY = os.getenv('TRONGRID_API_KEY')
TRON_NODE_URL = os.getenv('TRON_NODE_URL', 'https://api.trongrid.io')

# ФАЙЛЫ ДАННЫХ
USERS_DB = 'data/users.csv'
PAYMENTS_DB = 'data/payments.csv'
SUBSCRIPTIONS_DB = 'data/subscriptions.csv'
INVITES_DB = 'data/invites.csv'
LOG_FILE = 'logs/bot_activity.log'

# В реальном проекте сюда подставятся реальные ID из .env
CHANNELS = {
    'basic_1': -1,
    'basic_2': -2,
    'basic_3': -3,
    'standard_1': [-3, -2],
    'standard_2': -5,
    'standard_3': -6,
    'vip_1': -7,
    'vip_2': -8,
    'vip_3': -9,
    'premium_1': -10,
    'premium_2': -11,
    'premium_3': -12,
    'all': [
        -1, -2, -3, -4, -5, -6,
        -7, -8, -9, -10, -11
    ]
}

# ⚠️ ВАЖНО: Замените эти ID на ваши реальные ID каналов в production
# Эти значения служат только для демонстрации структуры проекта
TARIFFS = {
    'basic_1': {
        'name': 'Базовый 1',
        '30_days': 1900,
        'forever': 8000,
        'description': 'Описание базового тарифа 1'
    },
    'basic_2': {
        'name': 'Базовый 2',
        '30_days': 1990,
        'forever': 6999,
        'description': 'Описание базового тарифа 2'
    },
    'basic_3': {
        'name': 'Базовый 3',
        '30_days': 1111,
        'forever': 62222,
        'description': 'Описание базового тарифа 3'
    },
    'standard_1': {
        'name': 'Стандарт 1',
        '30_days': 63500,
        'forever': 825626,
        'description': 'Описание стандартного тарифа 1'
    },
    'standard_2': {
        'name': 'Стандарт 2',
        '30_days': 52353,
        'forever': 253525,
        'description': 'Описание стандартного тарифа 2'
    },
    'standard_3': {
        'name': 'Стандарт 3',
        '30_days': 2535,
        'forever': 23535,
        'description': 'Описание стандартного тарифа 3'
    },
    'vip_1': {
        'name': 'VIP 1',
        '30_days': 25235,
        'forever': 67235,
        'description': 'Описание VIP тарифа 1'
    },
    'vip_2': {
        'name': 'VIP 2',
        '30_days': 32423,
        'forever': 234234,
        'description': 'Описание VIP тарифа 2'
    },
    'vip_3': {
        'name': 'VIP 3',
        '30_days': 24234,
        'forever': 234234,
        'description': 'Описание VIP тарифа 3'
    },
    'premium_1': {
        'name': 'Премиум 1',
        '30_days': 234234,
        'forever': 234324,
        'description': 'Описание премиум тарифа 1'
    },
    'premium_2': {
        'name': 'Премиум 2',
        '30_days': 234234,
        'forever': 523423,
        'description': 'Описание премиум тарифа 2'
    },
    'premium_3': {
        'name': 'Премиум 3',
        '30_days': 234234,
        'forever': 234234,
        'description': 'Описание премиум тарифа 3'
    },
    'all': {
        'name': '✅ ВСЕ КАНАЛЫ',
        '30_days': None,  # Только навсегда
        'forever': 999999,
        'description': 'Доступ ко всем каналам навсегда'
    }
}