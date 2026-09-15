"""
PythonAnywhere uchun ishga tushirish fayli.

QANDAY ISHLATISH:
1. PythonAnywhere'da "Web" bo'limida yangi Flask ilova yarating (Manual configuration, Python 3.10)
2. Ochilgan "WSGI configuration file" faylining ICHINI TOZALAB,
   shu faylning TO'LIQ mazmunini o'sha yerga joylashtiring
3. Pastdagi PROJECT_PATH va WEBHOOK_DOMAIN ni o'zingizniki bilan almashtiring
4. "Web" sahifasida "Reload" tugmasini bosing

Bu fayl ishga tushganda:
- Flask ilovasini (admin panel + Mini App API) tayyorlaydi
- Telegramga "yangi xabar kelsa shu yerga yubor" deb bir marta xabar beradi (webhook)
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)

# ---- MUHIM: shu ikki qatorni o'zgartiring ----
PROJECT_PATH = "/home/SIZNING_USERNAME/shop_bot"
WEBHOOK_DOMAIN = "https://SIZNING_USERNAME.pythonanywhere.com"
# ------------------------------------------------

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)
os.chdir(PROJECT_PATH)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_PATH, ".env"))

# Mini App manzilini ham shu domenga moslab qo'yamiz
os.environ["WEBAPP_URL"] = WEBHOOK_DOMAIN.rstrip("/") + "/app"

from shared.models import init_db
init_db()

from admin.app import app as application
from admin.telegram_webhook import setup_webhook

setup_webhook(WEBHOOK_DOMAIN.rstrip("/") + "/telegram-webhook")
