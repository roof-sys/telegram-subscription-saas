"""Обработчики платежей (карты, СБП, USDT)"""
import time
import hashlib
import uuid
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
import httpx

from src.bot import dp, bot
from src.config import (
    TARIFFS, CHANNELS, ADMIN_ID, CRYPTO_EXCHANGE_RATE,
    CRYPTO_PAYMENT_ADDRESS, CRYPTO_PAYMENT_NETWORK,
    SHOP_ID, SHOP_SECRET, ACQUIRING_API_URL,
    TRONGRID_API_KEY, TRON_NODE_URL
)
from src.database.db_manager import (
    save_payment, update_payment_status, get_payment,
    save_subscription, save_invite, is_valid_invite, mark_invite_used
)

logger = logging.getLogger(__name__)


# ВЫБОР СПОСОБА ОПЛАТЫ

@dp.callback_query(lambda c: c.data.startswith("pay:"))
async def select_payment_method(callback: types.CallbackQuery):
    """Показывает меню выбора способа оплаты"""
    _, tariff_id, duration = callback.data.split(':')
    tariff = TARIFFS.get(tariff_id)

    if not tariff:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return

    # Определяем цену
    if duration == '30_days':
        price = tariff['30_days']
        tariff_name = f"{tariff['name']} (30 дней)"
    elif duration == 'forever':
        price = tariff['forever']
        tariff_name = f"{tariff['name']} (Навсегда)"
    else:
        await callback.answer("❌ Неверный срок подписки", show_alert=True)
        return

    # Кнопки с методами оплаты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Карта", callback_data=f"method:card:{tariff_id}:{duration}"),
            InlineKeyboardButton(text="📱 СБП", callback_data=f"method:sbp:{tariff_id}:{duration}")
        ],
        [
            InlineKeyboardButton(text="💎 USDT", callback_data=f"method:usdt:{tariff_id}:{duration}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"tariff:{tariff_id}")
        ]
    ])

    await callback.message.edit_text(
        f"📌 <b>{tariff_name}</b>\n\n"
        f"💵 Сумма: <b>{price}₽</b>\n\n"
        "Выберите способ оплаты:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback.answer()


# ОСНОВНАЯ ЛОГИКА ПЛАТЕЖЕЙ

@dp.callback_query(lambda c: c.data.startswith("method:"))
async def process_payment(callback: types.CallbackQuery):
    """Создает платеж в зависимости от выбранного метода"""
    try:
        _, method_type, tariff_id, duration = callback.data.split(':')
        tariff = TARIFFS.get(tariff_id)
        user = callback.from_user

        if not tariff:
            await callback.answer("❌ Тариф не найден", show_alert=True)
            return

        price_rub = tariff.get(duration)
        if price_rub is None:
            await callback.answer("❌ Неверный срок подписки", show_alert=True)
            return

        # Генерируем уникальный ID платежа
        payment_id = f"PAY_{user.id}_{int(time.time())}"

        # ОПЛАТА USDT
        if method_type == 'usdt':
            usdt_amount = price_rub / CRYPTO_EXCHANGE_RATE

            message_text = (
                f"💎 <b>Оплата USDT ({CRYPTO_PAYMENT_NETWORK})</b>\n\n"
                f"• Тариф: <b>{tariff['name']}</b>\n"
                f"• Сумма: <b>{usdt_amount:.2f} USDT</b> (~{price_rub}₽)\n"
                f"• Адрес: <code>{CRYPTO_PAYMENT_ADDRESS}</code>\n"
                f"• ID платежа: <code>{payment_id}</code>\n\n"
                "<b>Инструкция:</b>\n"
                "1. Отправьте <b>точную сумму</b> USDT на указанный адрес\n"
                "2. В <b>комментарии к платежу</b> укажите этот ID:\n"
                f"<code>{payment_id}</code>\n"
                "3. Нажмите кнопку <b>Проверить оплату</b> ниже\n\n"
                "⚠️ Без указания ID платеж может быть не распознан!"
            )

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"confirm:{payment_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"pay:{tariff_id}:{duration}")]
            ])

            # Сохраняем платеж в БД
            save_payment(
                user_id=user.id,
                username=user.username,
                tariff=f"{tariff['name']} ({'30 дней' if duration == '30_days' else 'Навсегда'})",
                amount=price_rub,
                payment_id=payment_id,
                method='USDT'
            )

            await callback.message.edit_text(
                text=message_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
            return

        # ОПЛАТА КАРТОЙ ИЛИ СБП
        payment_result = await create_payment_in_acquirer(
            amount_rub=price_rub,
            payment_id=payment_id,
            method='card' if method_type == 'card' else 'sbp',
            user_id=user.id
        )

        if not payment_result.get('success'):
            error_msg = payment_result.get('message', 'Неизвестная ошибка')
            await callback.answer(f"❌ Ошибка: {error_msg}", show_alert=True)
            return

        # Сохраняем платеж в БД
        save_payment(
            user_id=user.id,
            username=user.username,
            tariff=f"{tariff['name']} ({'30 дней' if duration == '30_days' else 'Навсегда'})",
            amount=price_rub,
            payment_id=payment_id,
            method='Карта' if method_type == 'card' else 'СБП',
            external_id=payment_result.get('external_id')
        )

        message_text = (
            f"💳 <b>Оплата {'картой' if method_type == 'card' else 'СБП'}</b>\n\n"
            f"• Тариф: <b>{tariff['name']}</b>\n"
            f"• Сумма: <b>{price_rub}₽</b>\n"
            f"• ID: <code>{payment_id}</code>\n\n"
            "Нажмите кнопку ниже для оплаты:"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_result['payment_url'])],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"confirm:{payment_id}")]
        ])

        await callback.message.edit_text(
            text=message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )

    except Exception as e:
        logger.error(f"Ошибка process_payment: {str(e)}", exc_info=True)
        await callback.answer(
            "⚠️ Ошибка при создании платежа. Попробуйте позже",
            show_alert=True
        )


# ПРОВЕРКА ОПЛАТЫ

@dp.callback_query(lambda c: c.data.startswith("confirm:"))
async def confirm_payment(callback: types.CallbackQuery):
    """Проверяет статус платежа и активирует подписку"""
    payment_id = callback.data.split(':')[1]

    try:
        # Получаем информацию о платеже из БД
        payment_data = get_payment(payment_id)

        if not payment_data:
            await callback.answer("❌ Платеж не найден", show_alert=True)
            return

        # Показываем, что начали проверку
        try:
            await callback.message.edit_text("🔍 Проверяем оплату...")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise

        # Проверяем платеж в зависимости от метода
        payment_ok = False

        if payment_data['method'] == 'USDT':
            usdt_amount = payment_data['amount'] / CRYPTO_EXCHANGE_RATE
            payment_ok = await check_usdt_payment(
                payment_id=payment_id,
                amount_usdt=usdt_amount
            )
        elif payment_data['external_id']:  # Карта/СБП
            payment_ok = await check_payment_in_acquirer(payment_data['external_id'])

        if payment_ok:
            # Обновляем статус платежа
            update_payment_status(payment_id, 'completed', payment_data.get('external_id'))

            # Сохраняем подписку
            save_subscription(
                payment_data['user_id'],
                payment_data['username'],
                payment_data['tariff'],
                payment_id
            )

            # Добавляем пользователя в каналы
            await add_user_to_channels(payment_data)

            # Отправляем админу уведомление
            await bot.send_message(
                ADMIN_ID,
                f"💸 <b>Новый платеж!</b>\n\n"
                f"👤 Пользователь: @{payment_data['username'] or 'нет username'}\n"
                f"📌 Тариф: {payment_data['tariff']}\n"
                f"💰 Сумма: {payment_data['amount']}₽\n"
                f"💳 Метод: {payment_data['method']}\n"
                f"🆔 ID: {payment_id}",
                parse_mode=ParseMode.HTML
            )

            # Показываем пользователю успех
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")]
            ])

            duration_text = "на 30 дней" if '30 дней' in payment_data['tariff'] else "навсегда"
            success_text = (
                f"✅ <b>Оплата подтверждена!</b>\n\n"
                f"🎉 Подписка активирована {duration_text}\n"
                f"📌 Тариф: <b>{payment_data['tariff']}</b>\n"
                f"💰 Сумма: <b>{payment_data['amount']}₽</b>\n\n"
                "Доступ к каналам уже выдан!"
            )

            try:
                await callback.message.edit_text(
                    text=success_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        else:
            # Платеж не найден
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Проверить снова", callback_data=f"confirm:{payment_id}")],
                [InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")]
            ])

            error_text = (
                "❌ <b>Оплата не найдена</b>\n\n"
                "Если вы уже оплатили, подождите несколько минут и попробуйте снова."
            )

            try:
                await callback.message.edit_text(
                    text=error_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise

    except Exception as e:
        logger.error(f"Ошибка в confirm_payment: {str(e)}", exc_info=True)
        await callback.answer("Произошла ошибка при проверке платежа", show_alert=True)
    finally:
        await callback.answer()


# ДОБАВЛЕНИЕ В КАНАЛЫ

async def add_user_to_channels(payment_data: dict):
    """Добавляет пользователя в соответствующие каналы"""
    user_id = payment_data['user_id']
    tariff_name = payment_data['tariff'].split()[0].lower()

    try:
        # Определяем, какие каналы нужны
        if tariff_name == 'all':
            message_text = "✅ Ваша подписка на ВСЕ КАНАЛЫ активирована!\n\n"
            message_text += "📢 Доступные каналы:\n"

            for channel_name, channel_id in CHANNELS.items():
                if channel_name != 'all':
                    if isinstance(channel_id, list):
                        for c_id in channel_id:
                            added = await add_user_to_channel(user_id, c_id)
                            if added:
                                message_text += f"  ✅ {TARIFFS.get(channel_name, {}).get('name', channel_name)}\n"
                            else:
                                invite_link = await generate_invite(user_id, c_id)
                                message_text += f"  🔗 {TARIFFS.get(channel_name, {}).get('name', channel_name)}: {invite_link}\n"
                    else:
                        added = await add_user_to_channel(user_id, channel_id)
                        if added:
                            message_text += f"  ✅ {TARIFFS.get(channel_name, {}).get('name', channel_name)}\n"
                        else:
                            invite_link = await generate_invite(user_id, channel_id)
                            message_text += f"  🔗 {TARIFFS.get(channel_name, {}).get('name', channel_name)}: {invite_link}\n"
        else:
            channel_id = CHANNELS.get(tariff_name)
            if channel_id:
                if isinstance(channel_id, list):
                    message_text = f"✅ Ваша подписка активирована!\n\nТариф: {payment_data['tariff']}\n\nДоступные каналы:\n"
                    for c_id in channel_id:
                        added = await add_user_to_channel(user_id, c_id)
                        if added:
                            message_text += f"  ✅ Канал добавлен\n"
                        else:
                            invite_link = await generate_invite(user_id, c_id)
                            message_text += f"  🔗 {invite_link}\n"
                else:
                    added = await add_user_to_channel(user_id, channel_id)
                    if added:
                        duration_text = "на 30 дней" if '30 дней' in payment_data['tariff'] else "навсегда"
                        message_text = (f"✅ Ваша подписка активирована {duration_text}!\n\n"
                                        f"Тариф: {payment_data['tariff']}\n\n"
                                        "Вы были добавлены в закрытый канал автоматически.")
                    else:
                        duration_text = "на 30 дней" if '30 дней' in payment_data['tariff'] else "навсегда"
                        invite_link = await generate_invite(user_id, channel_id)
                        message_text = (f"✅ Ваша подписка активирована {duration_text}!\n\n"
                                        f"Тариф: {payment_data['tariff']}\n\n"
                                        f"Ссылка для вступления: {invite_link}")
            else:
                message_text = "❌ Ошибка: канал не найден. Обратитесь к администратору."

        # Отправляем сообщение пользователю
        await bot.send_message(user_id, message_text)

    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя {user_id} в каналы: {e}")


async def add_user_to_channel(user_id: int, chat_id: int) -> bool:
    """Пытается добавить пользователя в канал"""
    try:
        await bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )
        logger.info(f"Пользователь {user_id} добавлен в канал {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Не удалось добавить {user_id} в канал {chat_id}: {e}")
        return False


async def generate_invite(user_id: int, chat_id: int) -> str:
    """Создает одноразовую инвайт-ссылку"""
    try:
        invite = await bot.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=1,
            expire_date=int((datetime.now() + timedelta(days=1)).timestamp())
        )

        save_invite(user_id, chat_id, invite.invite_link)
        logger.info(f"Инвайт создан для {user_id} в чат {chat_id}")
        return invite.invite_link
    except Exception as e:
        logger.error(f"Ошибка создания инвайта: {e}")
        return "Ошибка создания ссылки"


# ПЛАТЕЖНАЯ СИСТЕМА (КАРТЫ/СБП)

async def create_payment_in_acquirer(amount_rub: float, payment_id: str, method: str, user_id: int):
    """Создает платеж в эквайринге"""
    try:
        # Генерация подписи
        sign_str = f"{SHOP_ID}:{SHOP_SECRET}:{amount_rub}:{payment_id}"
        sign = hashlib.md5(sign_str.encode()).hexdigest().lower()

        request_data = {
            "shop_id": str(SHOP_ID),
            "amount": float(amount_rub),
            "merchant_order_id": payment_id,
            "sign": sign,
            "method": method,
            "user_id": str(user_id),
            "callback_url": f"https://yourdomain.com/callback/{payment_id}",
            "description": f"Оплата подписки (ID: {payment_id})"
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-ID": str(uuid.uuid4())
        }

        api_url = f"{ACQUIRING_API_URL}/api/merchant/order/create/by-api"

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Создание платежа: {payment_id}")

            response = await client.post(
                api_url,
                json=request_data,
                headers=headers
            )

            response.raise_for_status()
            data = response.json()

            if not data.get('success', False):
                error_msg = data.get('message', 'Неизвестная ошибка API')
                logger.error(f"Ошибка API: {error_msg}")
                return {'success': False, 'message': error_msg}

            payment_url = data.get('url') or data.get('payment_url')
            if not payment_url:
                logger.error("Платежная система не вернула URL")
                return {'success': False, 'message': 'Не получен URL для оплаты'}

            return {
                'success': True,
                'payment_url': payment_url,
                'external_id': data.get('payment_id') or data.get('external_id') or data.get('id')
            }

    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return {'success': False, 'message': str(e)}


async def check_payment_in_acquirer(external_id: str) -> bool:
    """Проверяет статус платежа в эквайринге"""
    try:
        if not external_id:
            return False

        sign_str = f"{SHOP_ID}:{SHOP_SECRET}:{external_id}"
        sign = hashlib.md5(sign_str.encode()).hexdigest().lower()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-sign": sign,
            "X-Request-ID": str(uuid.uuid4())
        }

        url = f"https://yourdomain.com/api/check/{external_id}"  # Замените на реальный URL

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Проверяем успешный статус
            if data.get('status') == 1 or data.get('paid') is True or data.get('state') == 'completed':
                logger.info(f"Платеж {external_id} подтвержден")
                return True

            return False

    except Exception as e:
        logger.error(f"Ошибка проверки платежа {external_id}: {e}")
        return False


# ПРОВЕРКА USDT

async def check_usdt_payment(payment_id: str, amount_usdt: float) -> bool:
    """Проверяет поступление USDT на кошелек"""
    try:
        headers = {
            'TRON-PRO-API-KEY': TRONGRID_API_KEY,
            'Content-Type': 'application/json'
        }

        params = {
            'contract_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',  # USDT контракт
            'only_confirmed': True,
            'limit': 20,
            'order_by': 'block_timestamp,desc',
            'min_timestamp': int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f'{TRON_NODE_URL}/v1/accounts/{CRYPTO_PAYMENT_ADDRESS}/transactions/trc20',
                headers=headers,
                params=params
            )

            if response.status_code != 200:
                logger.error(f"TronGrid API error: {response.status_code}")
                return False

            transactions = response.json().get('data', [])

            for tx in transactions:
                try:
                    is_incoming = tx['to'] == CRYPTO_PAYMENT_ADDRESS.lower()
                    is_usdt = tx['token_info']['symbol'] == 'USDT'
                    is_confirmed = tx.get('confirmed', True)

                    # Проверяем сумму (допуск 1%)
                    received_amount = float(tx['value']) / 10 ** 6
                    amount_match = received_amount >= amount_usdt * 0.99

                    # Ищем payment_id в memo или transaction_id
                    memo = tx.get('transaction_id', '') + tx.get('data', '')
                    has_payment_id = payment_id in memo

                    if all([is_incoming, is_usdt, is_confirmed, amount_match, has_payment_id]):
                        logger.info(f"Найден подходящий платеж: {tx['transaction_id']}")
                        return True

                except Exception as e:
                    continue

            return False

    except Exception as e:
        logger.error(f"Ошибка проверки USDT: {e}")
        return False


# ОБРАБОТЧИК ВСТУПЛЕНИЯ В КАНАЛ

from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import ChatMemberUpdated


@dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def handle_new_member(event: ChatMemberUpdated):
    """Проверяет, имеет ли пользователь право вступить в канал"""
    user_id = event.new_chat_member.user.id
    chat_id = event.chat.id

    # Проверяем, есть ли у пользователя активная подписка
    from src.database.db_manager import get_active_subscription
    subscription = get_active_subscription(user_id)

    if not subscription:
        # Нет подписки - баним
        try:
            await bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=int((datetime.now() + timedelta(minutes=1)).timestamp())
            )
            await bot.send_message(
                user_id,
                "⚠️ Доступ запрещен. У вас нет активной подписки."
            )
        except Exception as e:
            logger.error(f"Ошибка при бане пользователя {user_id}: {e}")
        return

    # Проверяем, действительна ли инвайт-ссылка
    logger.info(f"Пользователь {user_id} вступил в канал {chat_id}")