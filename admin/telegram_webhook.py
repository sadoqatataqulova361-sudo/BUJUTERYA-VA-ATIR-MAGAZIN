"""
Telegram bot uchun "webhook" rejimi.

Polling (doimiy so'rov yuborish) o'rniga - Telegram o'zi yangi xabar kelganda
bizning saytimizga POST so'rov yuboradi. Bu PythonAnywhere kabi "web app"
asosidagi hostinglarda ancha barqaror ishlaydi, chunki alohida fon jarayoni
(background thread) kerak emas.
"""
import asyncio
import logging
from flask import Blueprint, request

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update, BotCommand

from bot.config import BOT_TOKEN
from bot.handlers import catalog, order_flow

telegram_bp = Blueprint("telegram_webhook", __name__)

bot = None
dp = None

if BOT_TOKEN:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(catalog.router)
    dp.include_router(order_flow.router)
else:
    logging.warning("BOT_TOKEN topilmadi - Telegram webhook ishlamaydi")


@telegram_bp.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    """Telegram yangi xabar/tugma bosilganda shu manzilga xabar yuboradi."""
    if not bot or not dp:
        return "Bot sozlanmagan", 500
    try:
        data = request.get_json(force=True)
        update = Update.model_validate(data)
        asyncio.run(dp.feed_update(bot=bot, update=update))
    except Exception as e:
        logging.error(f"Webhook xatosi: {e}")
    return "OK"


def setup_webhook(webhook_url: str):
    """
    Bir martalik sozlash: Telegramga "yangi xabar kelsa shu manzilga yubor" deb aytadi.
    Bu funksiya WSGI fayl ishga tushganda bir marta chaqiriladi.
    """
    if not bot or not webhook_url:
        return

    async def _set():
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        await bot.set_my_commands([
            BotCommand(command="start", description="Katalogni ko'rish"),
            BotCommand(command="cart", description="Savatcham"),
            BotCommand(command="orders", description="Buyurtmalarim"),
        ])
        logging.info(f"Telegram webhook o'rnatildi: {webhook_url}")

    try:
        asyncio.run(_set())
    except Exception as e:
        logging.error(f"Webhook o'rnatishda xato: {e}")
