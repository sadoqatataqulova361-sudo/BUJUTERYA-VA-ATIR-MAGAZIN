import os
import sys
import uuid
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from shared.models import init_db, get_session, Category, Product, Order, AdminUser
from admin.webapp_api import api as webapp_api_blueprint
from admin.telegram_webhook import telegram_bp

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-o-zgartiring")
app.register_blueprint(webapp_api_blueprint)
app.register_blueprint(telegram_bp)

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------- Auth ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_session()
        try:
            user = db.query(AdminUser).filter_by(username=username).first()
        finally:
            db.close()

        if user and check_password_hash(user.password_hash, password):
            session["admin_id"] = user.id
            session["admin_username"] = user.username
            return redirect(url_for("products"))
        flash("Login yoki parol noto'g'ri", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- Mahsulotlar ----------------

@app.route("/")
@login_required
def index():
    return redirect(url_for("products"))


@app.route("/products")
@login_required
def products():
    db = get_session()
    try:
        items = db.query(Product).order_by(Product.id.desc()).all()
        categories = {c.id: c for c in db.query(Category).all()}
    finally:
        db.close()
    return render_template("products.html", products=items, categories=categories)


@app.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    db = get_session()
    try:
        categories = db.query(Category).order_by(Category.order).all()
        if request.method == "POST":
            photo_path = _handle_upload(request.files.get("photo"))
            product = Product(
                category_id=int(request.form["category_id"]),
                name=request.form["name"].strip(),
                description=request.form.get("description", "").strip(),
                price=float(request.form["price"]),
                old_price=float(request.form["old_price"]) if request.form.get("old_price") else None,
                photo_path=photo_path,
                in_stock="in_stock" in request.form,
                is_active="is_active" in request.form,
            )
            db.add(product)
            db.commit()
            flash("Mahsulot qo'shildi", "success")
            return redirect(url_for("products"))
    finally:
        db.close()
    return render_template("product_form.html", product=None, categories=categories)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    db = get_session()
    try:
        product = db.query(Product).get(product_id)
        categories = db.query(Category).order_by(Category.order).all()
        if not product:
            flash("Mahsulot topilmadi", "error")
            return redirect(url_for("products"))

        if request.method == "POST":
            product.category_id = int(request.form["category_id"])
            product.name = request.form["name"].strip()
            product.description = request.form.get("description", "").strip()
            product.price = float(request.form["price"])
            product.old_price = float(request.form["old_price"]) if request.form.get("old_price") else None
            product.in_stock = "in_stock" in request.form
            product.is_active = "is_active" in request.form

            new_photo = _handle_upload(request.files.get("photo"))
            if new_photo:
                product.photo_path = new_photo

            db.commit()
            flash("O'zgarishlar saqlandi", "success")
            return redirect(url_for("products"))

        return render_template("product_form.html", product=product, categories=categories)
    finally:
        db.close()


@app.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    db = get_session()
    try:
        product = db.query(Product).get(product_id)
        if product:
            db.delete(product)
            db.commit()
            flash("Mahsulot o'chirildi", "success")
    finally:
        db.close()
    return redirect(url_for("products"))


def _handle_upload(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(path)
    return path


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ---------------- Kategoriyalar ----------------

@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    db = get_session()
    try:
        if request.method == "POST":
            cat = Category(
                name=request.form["name"].strip(),
                emoji=request.form.get("emoji", "✨").strip() or "✨",
                order=int(request.form.get("order", 0) or 0),
                is_active=True,
            )
            db.add(cat)
            db.commit()
            flash("Kategoriya qo'shildi", "success")
            return redirect(url_for("categories"))

        items = db.query(Category).order_by(Category.order).all()
        return render_template("categories.html", categories=items)
    finally:
        db.close()


@app.route("/categories/<int:cat_id>/toggle", methods=["POST"])
@login_required
def category_toggle(cat_id):
    db = get_session()
    try:
        cat = db.query(Category).get(cat_id)
        if cat:
            cat.is_active = not cat.is_active
            db.commit()
    finally:
        db.close()
    return redirect(url_for("categories"))


@app.route("/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
def category_delete(cat_id):
    db = get_session()
    try:
        cat = db.query(Category).get(cat_id)
        if cat:
            db.delete(cat)
            db.commit()
            flash("Kategoriya o'chirildi", "success")
    finally:
        db.close()
    return redirect(url_for("categories"))


# ---------------- Buyurtmalar ----------------

STATUS_OPTIONS = ["yangi", "tasdiqlandi", "yetkazildi", "bekor_qilindi"]


@app.route("/orders")
@login_required
def orders():
    db = get_session()
    try:
        status_filter = request.args.get("status", "")
        q = db.query(Order).order_by(Order.created_at.desc())
        if status_filter:
            q = q.filter_by(status=status_filter)
        items = q.all()
        for o in items:
            _ = o.items  # lazy-load ichida bolib session yopilmasdan oldin
    finally:
        db.close()
    return render_template("orders.html", orders=items, statuses=STATUS_OPTIONS, current_status=status_filter)


@app.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def order_update_status(order_id):
    new_status = request.form.get("status")
    db = get_session()
    try:
        order = db.query(Order).get(order_id)
        if order and new_status in STATUS_OPTIONS:
            order.status = new_status
            db.commit()
            flash(f"Buyurtma #{order_id} holati yangilandi", "success")
    finally:
        db.close()
    return redirect(url_for("orders"))


# ---------------- Birinchi ishga tushirish: admin yaratish ----------------

def ensure_default_admin():
    """Agar birorta admin bo'lmasa, .env dagi login/parol bilan birinchi adminni yaratadi."""
    db = get_session()
    try:
        if db.query(AdminUser).count() == 0:
            username = os.getenv("ADMIN_USERNAME", "admin")
            password = os.getenv("ADMIN_PASSWORD", "admin123")
            db.add(AdminUser(username=username, password_hash=generate_password_hash(password)))
            db.commit()
            print(f"[i] Birinchi admin yaratildi -> login: {username} / parol: {password}")
    finally:
        db.close()


init_db()
ensure_default_admin()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
