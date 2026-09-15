import asyncio
import logging
import sys
import os

# shared/ papkasini import qilish uchun loyiha ildizini yo'lga qo'shamiz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import BOT_TOKEN
from bot.handlers import catalog, order_flow
from shared.models import init_db

logging.basicConfig(level=logging.INFO)


async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Katalogni ko'rish"),
        BotCommand(command="cart", description="Savatcham"),
        BotCommand(command="orders", description="Buyurtmalarim"),
    ])


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env faylida BOT_TOKEN=... qilib bot tokeningizni kiriting "
            "(BotFather orqali olinadi)."
        )

    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(catalog.router)
    dp.include_router(order_flow.router)

    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
