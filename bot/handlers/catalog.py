import os
import os
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.filters import CommandStart

from shared.models import get_session, Category, Product
from bot.keyboards import categories_kb, products_kb, product_detail_kb
from bot.config import SHOP_NAME, WEBAPP_URL

router = Router()


def format_price(value: float) -> str:
    return f"{int(value):,}".replace(",", " ") + " so'm"


def webapp_kb():
    if not WEBAPP_URL:
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        f"Assalomu alaykum! 👋\n\n"
        f"<b>{SHOP_NAME}</b>ga xush kelibsiz.\n"
    )
    kb = webapp_kb()
    if kb:
        text += "Quyidagi tugma orqali do'konni oching:"
        await message.answer(text, reply_markup=kb)
    else:
        text += "(Mini App manzili hali sozlanmagan - .env faylida WEBAPP_URL to'ldiring)"
        session = get_session()
        try:
            categories = session.query(Category).filter_by(is_active=True).order_by(Category.order).all()
        finally:
            session.close()
        await message.answer(text, reply_markup=categories_kb(categories) if categories else None)


@router.callback_query(F.data == "back_to_cats")
async def back_to_categories(callback: CallbackQuery):
    session = get_session()
    try:
        categories = session.query(Category).filter_by(is_active=True).order_by(Category.order).all()
    finally:
        session.close()
    await callback.message.answer("Bo'limni tanlang:", reply_markup=categories_kb(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        products = (
            session.query(Product)
            .filter_by(category_id=category_id, is_active=True)
            .all()
        )
        category = session.query(Category).get(category_id)
    finally:
        session.close()

    if not products:
        await callback.message.answer(f"'{category.name}' bo'limida hozircha mahsulot yo'q.")
        await callback.answer()
        return

    await callback.message.answer(
        f"<b>{category.name}</b> — mahsulotni tanlang:",
        reply_markup=products_kb(products, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        product = session.query(Product).get(product_id)
    finally:
        session.close()

    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    if product.has_discount:
        price_line = (
            f"<s>{format_price(product.old_price)}</s>  "
            f"<b>{format_price(product.price)}</b>  (-{product.discount_percent}%)"
        )
    else:
        price_line = f"<b>{format_price(product.price)}</b>"

    stock_line = "✅ Sotuvda bor" if product.in_stock else "❌ Hozircha yo'q"
    caption = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description or ''}\n\n"
        f"{price_line}\n\n"
        f"{stock_line}"
    )

    kb = product_detail_kb(product)

    if product.photo_path and os.path.exists(product.photo_path):
        photo = FSInputFile(product.photo_path)
        await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=kb)
    else:
        await callback.message.answer(caption, reply_markup=kb)
    await callback.answer()
