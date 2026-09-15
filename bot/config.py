import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")   # yangi buyurtma kelganda admin shu chatga xabar oladi
SHOP_NAME = os.getenv("SHOP_NAME", "Bizning Do'kon")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")  # Mini App manzili, masalan https://sizning-domen.com/app
