"""
Bu fayl bot va admin panelni BIRGA ishga tushiradi.
Bitta process/portga ruxsat beruvchi bepul hostinglar (Wispbyte va shunga o'xshash) uchun mo'ljallangan.

Admin panel (Flask) - alohida oqim (thread)da ishlaydi
Bot (aiogram) - asosiy oqimda ishlaydi
"""
import asyncio
import logging
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)


def run_admin_panel():
    """Flask admin panelni alohida oqimda ishga tushiradi."""
    from admin.app import app
    port = int(os.getenv("PORT", "5000"))
    # host="0.0.0.0" - serverdan tashqaridan ham kirish uchun
    # threaded=True - Cloudflare Tunnel bir vaqtda bir nechta so'rov yuborishi mumkin
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)


async def run_bot():
    """Telegram botni ishga tushiradi."""
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import BotCommand

    from bot.config import BOT_TOKEN
    from bot.handlers import catalog, order_flow
    from shared.models import init_db

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. Muhit o'zgaruvchilarida (Environment Variables) "
            "BOT_TOKEN qiymatini kiriting."
        )

    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(catalog.router)
    dp.include_router(order_flow.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Katalogni ko'rish"),
        BotCommand(command="cart", description="Savatcham"),
        BotCommand(command="orders", description="Buyurtmalarim"),
    ])

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def start_cloudflare_tunnel(port: int) -> str | None:
    """
    Cloudflare Tunnel (bepul) orqali serverga HTTPS manzil ochadi.
    Telegram Mini App'ga faqat HTTPS manzil orqali kirish mumkin,
    oddiy http:// manzil bilan ishlamaydi.
    """
    try:
        from pycloudflared import try_cloudflare
        result = try_cloudflare(port=port, verbose=False)
        logging.info(f"Cloudflare Tunnel ochildi: {result.tunnel}")
        return result.tunnel
    except Exception as e:
        logging.warning(f"Cloudflare Tunnel ochilmadi: {e}")
        return None


def wait_for_flask(port: int, timeout: int = 20):
    """Flask server so'rovlarga javob bera boshlaguncha kutadi."""
    import urllib.request
    import time as time_module
    deadline = time_module.time() + timeout
    while time_module.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/login", timeout=2)
            return True
        except Exception:
            time_module.sleep(0.5)
    return False


def main():
    port = int(os.getenv("PORT", "5000"))

    # Avval admin panelni (Flask) fon oqimida ishga tushiramiz
    admin_thread = threading.Thread(target=run_admin_panel, daemon=True)
    admin_thread.start()
    logging.info("Admin panel fon rejimida ishga tushdi")

    # Flask tayyor bo'lguncha kutamiz - shundan keyingina tunnel ochamiz
    if wait_for_flask(port):
        logging.info("Flask server javob bermoqda - tunnel ochilyapti")
    else:
        logging.warning("Flask serverni tekshirishda muammo, baribir tunnel ochishga urinamiz")

    # HTTPS tunnelni ochamiz va WEBAPP_URL'ni shu asosida sozlaymiz
    tunnel_url = start_cloudflare_tunnel(port)
    if tunnel_url:
        os.environ["WEBAPP_URL"] = tunnel_url.rstrip("/") + "/app"
        logging.info(f"Mini App manzili: {os.environ['WEBAPP_URL']}")
    else:
        logging.warning(
            "Tunnel ochilmadi - Mini App tugmasi botda ko'rinmaydi. "
            "Bot oddiy tugmalar bilan ishlaydi."
        )

    # Botni asosiy oqimda ishga tushiramiz
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
