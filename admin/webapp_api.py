"""
Mini App (Web App) uchun API.
Bu fayl admin/app.py ichiga ulanadi (blueprint sifatida).
Mini App shu API orqali kategoriya/mahsulot oladi va buyurtma yuboradi.
"""
import os
import requests
from flask import Blueprint, jsonify, request, send_from_directory

from shared.models import get_session, Category, Product, Order, OrderItem

api = Blueprint("api", __name__)

WEBAPP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")


def notify_admin(text: str):
    """Adminga Telegram orqali xabar yuboradi (aiogram shart emas, oddiy HTTP so'rov yetarli)."""
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass  # adminga xabar bormasa ham, buyurtma saqlanishi muhimroq


# ---------------- Mini App fayllarini xizmat qilish (HTML/CSS/JS) ----------------

@api.route("/app")
@api.route("/app/")
def webapp_index():
    return send_from_directory(WEBAPP_DIR, "index.html")


@api.route("/app/<path:filename>")
def webapp_static(filename):
    return send_from_directory(WEBAPP_DIR, filename)


# ---------------- API: Kategoriyalar ----------------

@api.route("/api/categories")
def api_categories():
    db = get_session()
    try:
        cats = db.query(Category).filter_by(is_active=True).order_by(Category.order).all()
        return jsonify([
            {"id": c.id, "name": c.name, "emoji": c.emoji}
            for c in cats
        ])
    finally:
        db.close()


# ---------------- API: Mahsulotlar ----------------

def _product_to_dict(p):
    return {
        "id": p.id,
        "category_id": p.category_id,
        "name": p.name,
        "description": p.description or "",
        "price": p.price,
        "old_price": p.old_price,
        "has_discount": p.has_discount,
        "discount_percent": p.discount_percent,
        "in_stock": p.in_stock,
        "photo_url": f"/uploads/{os.path.basename(p.photo_path)}" if p.photo_path else None,
    }


@api.route("/api/products")
def api_products():
    category_id = request.args.get("category_id", type=int)
    db = get_session()
    try:
        q = db.query(Product).filter_by(is_active=True)
        if category_id:
            q = q.filter_by(category_id=category_id)
        products = q.all()
        return jsonify([_product_to_dict(p) for p in products])
    finally:
        db.close()


@api.route("/api/product/<int:product_id>")
def api_product_detail(product_id):
    db = get_session()
    try:
        p = db.query(Product).get(product_id)
        if not p:
            return jsonify({"error": "topilmadi"}), 404
        return jsonify(_product_to_dict(p))
    finally:
        db.close()


# ---------------- API: Buyurtma berish ----------------

@api.route("/api/order", methods=["POST"])
def api_create_order():
    data = request.get_json(force=True, silent=True) or {}

    telegram_user_id = data.get("telegram_user_id")
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()
    comment = (data.get("comment") or "").strip()
    items = data.get("items") or []

    if not telegram_user_id or not name or not phone or not address or not items:
        return jsonify({"error": "Ma'lumotlar to'liq emas"}), 400

    db = get_session()
    try:
        total = 0.0
        order_items_data = []
        for item in items:
            product = db.query(Product).get(item.get("product_id"))
            if not product:
                continue
            qty = max(1, int(item.get("qty", 1)))
            total += product.price * qty
            order_items_data.append((product, qty))

        if not order_items_data:
            return jsonify({"error": "Savatcha bo'sh"}), 400

        order = Order(
            telegram_user_id=int(telegram_user_id),
            customer_name=name,
            phone=phone,
            address=address,
            total_price=total,
            status="yangi",
            comment=comment,
        )
        db.add(order)
        db.flush()

        for product, qty in order_items_data:
            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                price=product.price,
                quantity=qty,
            ))

        db.commit()
        order_id = order.id
        total_price = total
    finally:
        db.close()

    price_text = f"{int(total_price):,}".replace(",", " ") + " so'm"
    notify_admin(
        f"🆕 Yangi buyurtma #{order_id}\n"
        f"👤 {name} | 📱 {phone}\n"
        f"📍 {address}\n"
        f"💰 {price_text}"
        + (f"\n💬 {comment}" if comment else "")
    )

    return jsonify({"success": True, "order_id": order_id, "total_price": total_price})


# ---------------- API: Buyurtmalar tarixi (Profil bo'limi uchun) ----------------

@api.route("/api/orders")
def api_orders():
    telegram_user_id = request.args.get("user_id", type=int)
    if not telegram_user_id:
        return jsonify([])

    db = get_session()
    try:
        orders = (
            db.query(Order)
            .filter_by(telegram_user_id=telegram_user_id)
            .order_by(Order.created_at.desc())
            .all()
        )
        result = []
        for o in orders:
            result.append({
                "id": o.id,
                "status": o.status,
                "total_price": o.total_price,
                "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
                "items": [
                    {"name": it.product_name, "qty": it.quantity, "price": it.price}
                    for it in o.items
                ],
            })
        return jsonify(result)
    finally:
        db.close()


@api.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
def api_cancel_order(order_id):
    data = request.get_json(force=True, silent=True) or {}
    telegram_user_id = data.get("telegram_user_id")

    db = get_session()
    try:
        order = db.query(Order).get(order_id)
        if not order or order.telegram_user_id != int(telegram_user_id or 0):
            return jsonify({"error": "Ruxsat yo'q"}), 403
        if order.status not in ("yangi", "tasdiqlandi"):
            return jsonify({"error": "Bu buyurtmani bekor qilib bo'lmaydi"}), 400
        order.status = "bekor_qilindi"
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()
