from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


def categories_kb(categories):
    """Kategoriyalar ro'yxatini tugmalar shaklida chiqaradi."""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"cat:{cat.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(products, category_id):
    """Bitta kategoriya ichidagi mahsulotlar ro'yxati."""
    buttons = []
    for p in products:
        price_text = f"{int(p.price):,} so'm".replace(",", " ")
        if p.has_discount:
            price_text = f"🔥 {price_text}"
        buttons.append([InlineKeyboardButton(
            text=f"{p.name} — {price_text}",
            callback_data=f"prod:{p.id}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Kategoriyalarga qaytish", callback_data="back_to_cats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(product):
    buttons = [
        [InlineKeyboardButton(text="🛒 Savatchaga qo'shish", callback_data=f"add:{product.id}")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"cat:{product.category_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_kb(items):
    """Savatcha ro'yxati: har bir mahsulot uchun +/- va o'chirish tugmalari."""
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(text="➖", callback_data=f"dec:{item['product_id']}"),
            InlineKeyboardButton(text=f"{item['name']} x{item['qty']}", callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"inc:{item['product_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"rm:{item['product_id']}"),
        ])
    if items:
        buttons.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout")])
        buttons.append([InlineKeyboardButton(text="🗑 Savatchani tozalash", callback_data="clear_cart")])
    buttons.append([InlineKeyboardButton(text="🛍 Katalogga qaytish", callback_data="back_to_cats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def phone_request_kb():
    """Telefon raqamini bitta tugma bilan yuborish."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_kb():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()


def order_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")],
    ])


def my_orders_kb(orders):
    buttons = []
    for o in orders:
        buttons.append([InlineKeyboardButton(
            text=f"#{o.id} — {o.status} — {int(o.total_price):,} so'm".replace(",", " "),
            callback_data=f"order_detail:{o.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_order_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Buyurtmani bekor qilish", callback_data=f"cancel_my_order:{order_id}")],
    ])
