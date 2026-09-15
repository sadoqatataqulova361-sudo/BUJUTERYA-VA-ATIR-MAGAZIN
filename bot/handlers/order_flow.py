from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from shared.models import get_session, Product, Order, OrderItem
from bot.keyboards import (
    cart_kb, phone_request_kb, remove_kb, order_confirm_kb,
    my_orders_kb, cancel_order_kb, categories_kb
)
from bot.config import ADMIN_CHAT_ID
from bot.handlers.catalog import format_price

router = Router()

# Soddalik uchun savatchani xotirada saqlaymiz: {user_id: [{"product_id", "name", "price", "qty"}]}
CARTS: dict[int, list[dict]] = {}


class Checkout(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()


def _cart_total(user_id: int) -> float:
    return sum(i["price"] * i["qty"] for i in CARTS.get(user_id, []))


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        product = session.query(Product).get(product_id)
    finally:
        session.close()

    if not product or not product.in_stock:
        await callback.answer("Bu mahsulot hozircha mavjud emas", show_alert=True)
        return

    cart = CARTS.setdefault(callback.from_user.id, [])
    for item in cart:
        if item["product_id"] == product_id:
            item["qty"] += 1
            break
    else:
        cart.append({"product_id": product_id, "name": product.name, "price": product.price, "qty": 1})

    await callback.answer("✅ Savatchaga qo'shildi")


@router.message(F.text == "/cart")
@router.callback_query(F.data == "show_cart")
async def show_cart(event):
    user_id = event.from_user.id
    cart = CARTS.get(user_id, [])
    if not cart:
        text = "Savatchangiz bo'sh. Katalogdan mahsulot tanlang 🛍"
    else:
        lines = ["<b>🛒 Savatchangiz:</b>\n"]
        for item in cart:
            lines.append(f"• {item['name']} — {item['qty']} x {format_price(item['price'])}")
        lines.append(f"\n<b>Jami: {format_price(_cart_total(user_id))}</b>")
        text = "\n".join(lines)

    kb = cart_kb(cart)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("inc:"))
async def inc_item(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    cart = CARTS.get(callback.from_user.id, [])
    for item in cart:
        if item["product_id"] == product_id:
            item["qty"] += 1
    await callback.answer()
    await _refresh_cart_message(callback)


@router.callback_query(F.data.startswith("dec:"))
async def dec_item(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    cart = CARTS.get(callback.from_user.id, [])
    for item in cart:
        if item["product_id"] == product_id:
            item["qty"] -= 1
    CARTS[callback.from_user.id] = [i for i in cart if i["qty"] > 0]
    await callback.answer()
    await _refresh_cart_message(callback)


@router.callback_query(F.data.startswith("rm:"))
async def remove_item(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    cart = CARTS.get(callback.from_user.id, [])
    CARTS[callback.from_user.id] = [i for i in cart if i["product_id"] != product_id]
    await callback.answer("O'chirildi")
    await _refresh_cart_message(callback)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    CARTS[callback.from_user.id] = []
    await callback.answer("Savatcha tozalandi")
    await _refresh_cart_message(callback)


async def _refresh_cart_message(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart = CARTS.get(user_id, [])
    if not cart:
        text = "Savatchangiz bo'sh. Katalogdan mahsulot tanlang 🛍"
    else:
        lines = ["<b>🛒 Savatchangiz:</b>\n"]
        for item in cart:
            lines.append(f"• {item['name']} — {item['qty']} x {format_price(item['price'])}")
        lines.append(f"\n<b>Jami: {format_price(_cart_total(user_id))}</b>")
        text = "\n".join(lines)
    try:
        await callback.message.edit_text(text, reply_markup=cart_kb(cart))
    except Exception:
        await callback.message.answer(text, reply_markup=cart_kb(cart))


# ---------------- Buyurtma berish (checkout) ----------------

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    cart = CARTS.get(callback.from_user.id, [])
    if not cart:
        await callback.answer("Savatchangiz bo'sh", show_alert=True)
        return
    await state.set_state(Checkout.waiting_name)
    await callback.message.answer("Ismingizni kiriting:")
    await callback.answer()


@router.message(Checkout.waiting_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Checkout.waiting_phone)
    await message.answer(
        "Telefon raqamingizni yuboring (tugmani bosing yoki qo'lda kiriting):",
        reply_markup=phone_request_kb()
    )


@router.message(Checkout.waiting_phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(Checkout.waiting_address)
    await message.answer("Yetkazib berish manzilini kiriting (shahar, tuman, ko'cha):", reply_markup=remove_kb())


@router.message(Checkout.waiting_phone, F.text)
async def get_phone_text(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Checkout.waiting_address)
    await message.answer("Yetkazib berish manzilini kiriting (shahar, tuman, ko'cha):", reply_markup=remove_kb())


@router.message(Checkout.waiting_address)
async def get_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    cart = CARTS.get(user_id, [])
    total = _cart_total(user_id)

    lines = ["<b>Buyurtmangizni tekshiring:</b>\n"]
    for item in cart:
        lines.append(f"• {item['name']} — {item['qty']} x {format_price(item['price'])}")
    lines.append(f"\n<b>Jami: {format_price(total)}</b>")
    lines.append(f"\n👤 {data['name']}")
    lines.append(f"📱 {data['phone']}")
    lines.append(f"📍 {data['address']}")

    await message.answer("\n".join(lines), reply_markup=order_confirm_kb())


@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = callback.from_user.id
    cart = CARTS.get(user_id, [])
    if not cart:
        await callback.answer("Savatcha bo'sh qoldi", show_alert=True)
        await state.clear()
        return

    session = get_session()
    try:
        order = Order(
            telegram_user_id=user_id,
            customer_name=data["name"],
            phone=data["phone"],
            address=data["address"],
            total_price=_cart_total(user_id),
            status="yangi",
        )
        session.add(order)
        session.flush()  # order.id olish uchun

        for item in cart:
            session.add(OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                product_name=item["name"],
                price=item["price"],
                quantity=item["qty"],
            ))
        session.commit()
        order_id = order.id
    finally:
        session.close()

    order_total = sum(i["price"] * i["qty"] for i in cart)
    CARTS[user_id] = []
    await state.clear()

    await callback.message.answer(
        f"✅ Buyurtmangiz qabul qilindi! Raqami: <b>#{order_id}</b>\n\n"
        f"Tez orada operatorimiz siz bilan bog'lanadi.\n"
        f"Buyurtmalaringizni /orders buyrug'i orqali kuzatib borishingiz mumkin."
    )
    await callback.answer()

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"🆕 Yangi buyurtma #{order_id}\n"
                f"👤 {data['name']} | 📱 {data['phone']}\n"
                f"📍 {data['address']}\n"
                f"💰 {format_price(order_total)}"
            )
        except Exception:
            pass


@router.callback_query(F.data == "cancel_order")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Buyurtma bekor qilindi.", reply_markup=remove_kb())
    await callback.answer()


# ---------------- Mening buyurtmalarim ----------------

@router.message(F.text == "/orders")
async def my_orders(message: Message):
    session = get_session()
    try:
        orders = (
            session.query(Order)
            .filter_by(telegram_user_id=message.from_user.id)
            .order_by(Order.created_at.desc())
            .all()
        )
    finally:
        session.close()

    if not orders:
        await message.answer("Sizda hali buyurtmalar yo'q.")
        return

    await message.answer("Buyurtmalaringiz:", reply_markup=my_orders_kb(orders))


@router.callback_query(F.data.startswith("order_detail:"))
async def order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        order = session.query(Order).get(order_id)
        items = order.items if order else []
        lines = [f"<b>Buyurtma #{order.id}</b> — holati: <b>{order.status}</b>\n"]
        for it in items:
            lines.append(f"• {it.product_name} — {it.quantity} x {format_price(it.price)}")
        lines.append(f"\n<b>Jami: {format_price(order.total_price)}</b>")
        lines.append(f"📍 {order.address}")
        text = "\n".join(lines)
        can_cancel = order.status in ("yangi", "tasdiqlandi")
    finally:
        session.close()

    kb = cancel_order_kb(order_id) if can_cancel else None
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_my_order:"))
async def cancel_my_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        order = session.query(Order).get(order_id)
        if order and order.telegram_user_id == callback.from_user.id and order.status in ("yangi", "tasdiqlandi"):
            order.status = "bekor_qilindi"
            session.commit()
            await callback.answer("Buyurtma bekor qilindi", show_alert=True)
            await callback.message.answer(f"❌ Buyurtma #{order_id} bekor qilindi.")
        else:
            await callback.answer("Bu buyurtmani bekor qilib bo'lmaydi", show_alert=True)
    finally:
        session.close()
